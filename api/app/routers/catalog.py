"""Movies, search and genres."""
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import user_id_from
from app.db import get_db
from app.models.catalog import normalize_sql
from app.services import recommender as rec
from app.services.movies import cards, detail

router = APIRouter(tags=["catalog"])


@router.get("/movies/{movie_id}")
def movie(movie_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    uid = user_id_from(request)
    d = detail(db, movie_id, uid)
    if d is None:
        raise HTTPException(404, "Unknown movie")
    if uid is not None and rec.artifacts_ready():
        engine = rec.load_engine(db)
        st = rec.user_state(db, uid, engine)
        row = engine.cat.row_of.get(movie_id)
        if row is not None:
            scores = engine.rail_scores(st)
            raw = float(scores[row]) if np.isfinite(scores[row]) else None
            d["match_pct"] = engine.match(st.stage, raw) if raw is not None else None
            shares = _shares(engine, st, row)
            d["why"] = engine.reasons(st, row, shares)
    return d


def _shares(engine, st, row) -> dict:
    """Per-source share of a single film's catalog-wide hybrid score (for Why This on any page)."""
    scores = engine.scores(st)
    w = engine.weights[st.stage]
    parts = {}
    for s, v in scores.items():
        ok = np.isfinite(v)
        if not ok[row] or not w.get(s):
            continue
        pct = (np.argsort(np.argsort(v[ok])) + 1) / ok.sum()
        parts[s] = w[s] * float(pct[np.nonzero(ok)[0].tolist().index(row)])
    total = sum(parts.values()) or 1.0
    return {s: p / total for s, p in parts.items()}


@router.get("/movies/{movie_id}/similar")
def similar(movie_id: int, request: Request, db: Session = Depends(get_db)) -> dict:
    if not rec.artifacts_ready():
        return {"items": []}
    engine = rec.load_engine(db)
    row = engine.cat.row_of.get(movie_id)
    if row is None:
        raise HTTPException(404, "Unknown movie")
    ids = [int(engine.cat.movie_ids[r]) for r in engine.similar(row)]
    return {"items": cards(db, ids, user_id_from(request))}


@router.get("/movies")
def discover(request: Request, genre: str | None = None, lang: str | None = None, decade: int | None = None,
             runtime: str | None = None, country: str | None = None, min_rating: float | None = None,
             sort: str = "popular", page: int = 1, db: Session = Depends(get_db)) -> dict:
    where, p = ["true"], {}
    if genre:
        where.append("m.id IN (SELECT mg.movie_id FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id WHERE g.slug = :genre)")
        p["genre"] = genre
    if lang:
        where.append("m.original_language = :lang"); p["lang"] = lang
    if decade:
        where.append("m.year BETWEEN :d AND :d + 9"); p["d"] = decade
    if runtime in ("short", "medium", "long"):
        where.append({"short": "m.runtime_min < 90", "medium": "m.runtime_min BETWEEN 90 AND 120",
                      "long": "m.runtime_min > 120"}[runtime])
    if country:
        where.append(":country = ANY(m.countries)"); p["country"] = country
    if min_rating:
        where.append("m.popularity_score >= :mr"); p["mr"] = min_rating
    order = {"popular": "m.tmdb_vote_count DESC NULLS LAST", "rating": "m.popularity_score DESC NULLS LAST",
             "newest": "m.release_date DESC NULLS LAST", "title": "m.title"}.get(sort, "m.tmdb_vote_count DESC NULLS LAST")
    p.update(limit=40, offset=(max(page, 1) - 1) * 40)
    ids = [r[0] for r in db.execute(text(f"SELECT m.id FROM movies m WHERE {' AND '.join(where)} ORDER BY {order} LIMIT :limit OFFSET :offset"), p)]
    total = db.execute(text(f"SELECT count(*) FROM movies m WHERE {' AND '.join(where)}"), p).scalar()
    return {"items": cards(db, ids, user_id_from(request)), "total": total, "page": page}


SEARCH_LIMIT = 60
FUZZY_BELOW = 10          # fuzzy title matches are added only when the exact search finds fewer films
FUZZY_MIN_CHARS = 3       # shorter queries have too few trigrams to compare
FUZZY_THRESHOLD = 0.6     # pg_trgm word_similarity of the query to the closest part of a title


@router.get("/search")
def search(q: str, request: Request, db: Session = Depends(get_db)) -> dict:
    """Title, cast and director through the search_vector; genre and language by name.

    Titles are also compared after normalization (no dots or apostrophes, punctuation as spaces), so
    "LA confidential" finds "L.A. Confidential". Exact title matches rank first, then titles that start
    with the query (a leading "The" is optional), most-voted first within each; the rest by text rank.
    If that finds fewer than FUZZY_BELOW films, trigram similarity on the normalized title adds typo
    matches ("horrible bossses"), best match first, with TMDB vote count as the tie-break."""
    q = q.strip()
    if not q:
        return {"items": []}
    # text() would read ":alnum" in the regex as a bind parameter, so those colons are escaped.
    qn = "(" + normalize_sql(":q").replace("[:alnum:]", r"[\:alnum\:]") + ")"
    ids = [r[0] for r in db.execute(text(f"""
        WITH hits AS (
            SELECT m.id, m.tmdb_vote_count AS votes,
                   ts_rank(m.search_vector, plainto_tsquery('simple', :q)) AS rank,
                   CASE WHEN m.title_norm IN ({qn}, 'the ' || {qn}) THEN 0
                        WHEN m.title_norm LIKE {qn} || ' %' OR m.title_norm LIKE 'the ' || {qn} || ' %' THEN 1
                        ELSE 2 END AS tier
            FROM movies m
            WHERE m.search_vector @@ plainto_tsquery('simple', :q)
               OR m.id IN (SELECT mg.movie_id FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id WHERE g.name ILIKE :like)
               OR m.title ILIKE :like
               OR ({qn} <> '' AND m.title_norm LIKE '%' || {qn} || '%'))
        SELECT id FROM hits
        ORDER BY tier, CASE WHEN tier < 2 THEN votes END DESC NULLS LAST, rank DESC, votes DESC NULLS LAST
        LIMIT :limit"""), {"q": q, "like": f"%{q}%", "limit": SEARCH_LIMIT})]
    if len(ids) < FUZZY_BELOW and len(q) >= FUZZY_MIN_CHARS:
        # Sets the threshold of the indexed <% operator for this transaction only.
        db.execute(text("SELECT set_config('pg_trgm.word_similarity_threshold', :t, true)"),
                   {"t": str(FUZZY_THRESHOLD)})
        fuzzy = db.execute(text(f"""
            SELECT m.id FROM movies m
            WHERE {qn} <% m.title_norm
            ORDER BY round(greatest(word_similarity({qn}, m.title_norm), similarity({qn}, m.title_norm))::numeric, 2) DESC,
                     m.tmdb_vote_count DESC NULLS LAST
            LIMIT :limit"""), {"q": q, "limit": SEARCH_LIMIT})
        seen = set(ids)
        ids += [r[0] for r in fuzzy if r[0] not in seen][:SEARCH_LIMIT - len(ids)]
    return {"items": cards(db, ids, user_id_from(request))}


@router.get("/genres")
def genres(db: Session = Depends(get_db)) -> dict:
    rows = db.execute(text("""SELECT g.id, g.name, g.slug, count(mg.movie_id) AS films,
        (SELECT m.backdrop_path FROM movies m JOIN movie_genres x ON x.movie_id = m.id WHERE x.genre_id = g.id
         AND m.backdrop_path IS NOT NULL ORDER BY m.tmdb_vote_count DESC NULLS LAST LIMIT 1) AS backdrop
        FROM genres g LEFT JOIN movie_genres mg ON mg.genre_id = g.id GROUP BY g.id ORDER BY g.name""")).mappings()
    return {"genres": [dict(r) for r in rows]}


@router.get("/genres/{slug}/movies")
def genre_movies(slug: str, request: Request, page: int = 1, db: Session = Depends(get_db)) -> dict:
    """A genre page ranks its films FOR THIS USER with the hybrid score (spec 8.3)."""
    g = db.execute(text("SELECT id, name FROM genres WHERE slug = :s"), {"s": slug}).first()
    if g is None:
        raise HTTPException(404, "Unknown genre")
    uid = user_id_from(request)
    if uid is None or not rec.artifacts_ready():
        return discover(request, genre=slug, page=page, db=db) | {"genre": g[1]}
    engine = rec.load_engine(db)
    st = rec.user_state(db, uid, engine)
    scores = engine.rail_scores(st)
    rows = [r for r in np.argsort(-scores) if g[1] in engine.cat.genres[r] and np.isfinite(scores[r])]
    start = (max(page, 1) - 1) * 40
    pick = rows[start:start + 40]
    extra = {int(engine.cat.movie_ids[r]): {"score": float(scores[r]), "match_pct": engine.match(st.stage, float(scores[r]))}
             for r in pick}
    return {"genre": g[1], "items": cards(db, list(extra), uid, extra), "total": len(rows), "page": page}