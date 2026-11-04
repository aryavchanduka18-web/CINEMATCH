"""Import ratings exported from Letterboxd (ratings.csv) or IMDb (ratings.csv).

The browser reads the file and sends its text, so nothing is stored but the matched ratings. IMDb rows match on
the IMDb id; Letterboxd rows match on the normalized title and the year (one year either way, the exact year
first). Films already rated on FlickRaven keep the FlickRaven rating. Imported ratings count like any other
rating (they move the user out of the new-user stage and shape every recommendation).
"""
import csv
import io
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.ratelimit import IMPORT
from app.services import events as ev

router = APIRouter(prefix="/me/import", tags=["import"])

MAX_ROWS = 10_000
MAX_CHARS = 4_000_000          # a 10,000-film Letterboxd export is about 1 MB


class ImportBody(BaseModel):
    csv: str = Field(max_length=MAX_CHARS)


def normalize(title: str) -> str:
    """Same rule as the database's movies.title_norm (app.models.catalog.normalize_sql)."""
    t = re.sub(r"[.'’`]", "", title.lower())
    return re.sub(r"[\W_]+", " ", t).strip()


def parse(raw: str) -> tuple[str, list[dict]]:
    """('letterboxd' | 'imdb', rows with key + rating 1..10). Rows without a usable rating are skipped."""
    reader = csv.DictReader(io.StringIO(raw.lstrip("﻿")))
    head = {h.strip() for h in (reader.fieldnames or [])}
    if {"Const", "Your Rating"} <= head:
        kind = "imdb"
    elif {"Name", "Year", "Rating"} <= head:
        kind = "letterboxd"
    elif {"Name", "Year"} <= head:
        raise HTTPException(422, "This Letterboxd file has no ratings. Upload ratings.csv from your Letterboxd export.")
    else:
        raise HTTPException(422, "This does not look like a Letterboxd or IMDb ratings file.")
    rows = []
    for i, r in enumerate(reader):
        if i >= MAX_ROWS:
            break
        r = {(k or "").strip(): (v or "").strip() for k, v in r.items()}
        try:
            if kind == "imdb":
                if (r.get("Title Type") or "Movie").lower() not in ("movie", "tvmovie", "tv movie", "video"):
                    continue
                rating = int(float(r["Your Rating"]))
                rows.append({"imdb": r["Const"], "title": r.get("Title", ""), "rating": rating})
            else:
                rating = round(float(r["Rating"]) * 2)       # 0.5..5 stars -> 1..10
                rows.append({"title": r["Name"], "norm": normalize(r["Name"]),
                             "year": int(r["Year"]) if r.get("Year") else None, "rating": rating})
        except (KeyError, ValueError):
            continue
    return kind, [r for r in rows if 1 <= r["rating"] <= 10]


def match(db: Session, kind: str, rows: list[dict]) -> list[tuple[dict, int | None]]:
    if kind == "imdb":
        ids = list({r["imdb"] for r in rows})
        found = dict(db.execute(text("SELECT imdb_id, id FROM movies WHERE imdb_id = ANY(:ids)"), {"ids": ids}).all())
        return [(r, found.get(r["imdb"])) for r in rows]
    norms = list({r["norm"] for r in rows if r["norm"]})
    by_title: dict[str, list[tuple[int, int | None, int]]] = {}
    for mid, norm, year, votes in db.execute(text("""SELECT id, title_norm, year, coalesce(tmdb_vote_count, 0)
            FROM movies WHERE title_norm = ANY(:t)"""), {"t": norms}):
        by_title.setdefault(norm, []).append((mid, year, votes))
    out = []
    for r in rows:
        cands = by_title.get(r["norm"], [])
        if r["year"] is not None:
            cands = [c for c in cands if c[1] is not None and abs(c[1] - r["year"]) <= 1]
            cands.sort(key=lambda c: (abs(c[1] - r["year"]), -c[2]))
        else:
            cands.sort(key=lambda c: -c[2])
        out.append((r, cands[0][0] if cands else None))
    return out


@router.post("")
def import_ratings(body: ImportBody, user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    key = f"user:{user['id']}"
    IMPORT.check(key)
    IMPORT.fail(key)
    kind, rows = parse(body.csv)
    if not rows:
        raise HTTPException(422, "No ratings found in this file.")
    matched = match(db, kind, rows)
    rated = {m for (m,) in db.execute(text("SELECT movie_id FROM ratings WHERE user_id = :u"), {"u": user["id"]})}
    imported, kept, seen, unmatched = 0, 0, set(), []
    for r, mid in matched:
        if mid is None:
            unmatched.append(r["title"])
            continue
        if mid in seen:
            continue
        seen.add(mid)
        if mid in rated:
            kept += 1
            continue
        ev.set_rating(db, user["id"], mid, r["rating"], f"import:{kind}")
        imported += 1
    db.commit()
    return {"source": kind, "rows": len(rows), "imported": imported, "already_rated": kept,
            "not_found": len(unmatched), "not_found_examples": unmatched[:8]}
