"""Themed collections for Home (Rom-Com, Crime Thriller, ...), defined only by real catalog data.

A film belongs to a collection when it has all of the collection's genres (`all_genres`), at least one of
`keywords` if given, plus optional language / year / runtime limits. Inside a collection, films are ordered
by the user's own hybrid score when the engine can score them, otherwise by display popularity; a few
well-known titles can be pinned to the front (`pinned`: real titles, only shown if they are members).
A collection is offered only with at least MIN_FILMS films.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

MIN_FILMS = 6

COLLECTIONS = [
    {"key": "rom-com", "title": "Rom-Com", "all_genres": ["Romance", "Comedy"],
     "pinned": [("Leap Year", 2010), ("The Proposal", 2009), ("How to Lose a Guy in 10 Days", 2003),
                ("Notting Hill", 1999), ("Crazy Rich Asians", 2018), ("27 Dresses", 2008)]},
    {"key": "crime-thriller", "title": "Crime Thriller", "all_genres": ["Crime", "Thriller"]},
    {"key": "sci-fi-adventure", "title": "Sci-Fi Adventure", "all_genres": ["Science Fiction", "Adventure"]},
    {"key": "family-animation", "title": "Family Animation", "all_genres": ["Family", "Animation"]},
    {"key": "psychological-thriller", "title": "Psychological Thriller", "all_genres": ["Thriller"],
     "keywords": ["psychological thriller", "psychological"]},
    {"key": "war-drama", "title": "War Drama", "all_genres": ["War", "Drama"]},
    {"key": "action-comedy", "title": "Action Comedy", "all_genres": ["Action", "Comedy"]},
    {"key": "historical-epic", "title": "Historical Epic", "all_genres": ["History"], "min_runtime": 140},
    {"key": "heist", "title": "Heist Films", "keywords": ["heist"]},
    {"key": "true-stories", "title": "Based on a True Story", "keywords": ["based on true story"]},
    {"key": "superheroes", "title": "Superheroes", "keywords": ["superhero"]},
    {"key": "time-travel", "title": "Time Travel", "keywords": ["time travel"]},
    {"key": "coming-of-age", "title": "Coming of Age", "keywords": ["coming of age"]},
    {"key": "martial-arts", "title": "Martial Arts", "keywords": ["martial arts"]},
    {"key": "horror-comedy", "title": "Horror Comedy", "all_genres": ["Horror", "Comedy"]},
    {"key": "retro-hindi", "title": "Retro Hindi Classics", "language": "hi", "max_year": 1999},
    {"key": "anime", "title": "Anime Films", "all_genres": ["Animation"], "language": "ja"},
    {"key": "korean-thrillers", "title": "Korean Thrillers", "all_genres": ["Thriller"], "language": "ko"},
]
BY_KEY = {c["key"]: c for c in COLLECTIONS}


def member_ids(db: Session, c: dict) -> list[int]:
    """Films in the collection, most popular first (the order used when nothing personal is known)."""
    where, p = ["true"], {}
    for i, g in enumerate(c.get("all_genres", [])):
        where.append(f"EXISTS (SELECT 1 FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id "
                     f"WHERE mg.movie_id = m.id AND g.name = :g{i})")
        p[f"g{i}"] = g
    if c.get("keywords"):
        where.append("EXISTS (SELECT 1 FROM movie_keywords mk JOIN keywords k ON k.id = mk.keyword_id "
                     "WHERE mk.movie_id = m.id AND k.name = ANY(:kw))")
        p["kw"] = c["keywords"]
    if c.get("language"):
        where.append("m.original_language = :lang")
        p["lang"] = c["language"]
    if c.get("max_year"):
        where.append("m.year <= :maxy")
        p["maxy"] = c["max_year"]
    if c.get("min_runtime"):
        where.append("m.runtime_min >= :minrt")
        p["minrt"] = c["min_runtime"]
    return [r[0] for r in db.execute(text(f"""SELECT m.id FROM movies m WHERE {' AND '.join(where)}
        ORDER BY m.popularity_score DESC NULLS LAST, m.tmdb_vote_count DESC NULLS LAST"""), p)]


def pinned_ids(db: Session, c: dict, members: list[int]) -> list[int]:
    allowed, found = set(members), []
    for title, year in c.get("pinned", []):
        mid = db.execute(text("""SELECT id FROM movies WHERE title = :t AND year = :y
                                 ORDER BY tmdb_vote_count DESC NULLS LAST LIMIT 1"""), {"t": title, "y": year}).scalar()
        if mid is not None and mid in allowed:
            found.append(mid)
    return found


def ordered(db: Session, c: dict, match: dict[int, dict], members: list[int] | None = None) -> list[int]:
    """Pinned titles first, then films the engine scores for this user (best first), then the rest by popularity."""
    members = member_ids(db, c) if members is None else members
    pins = pinned_ids(db, c, members)
    rest = [i for i in members if i not in set(pins)]
    scored = sorted((i for i in rest if i in match), key=lambda i: -match[i]["score"])
    return pins + scored + [i for i in rest if i not in match]
