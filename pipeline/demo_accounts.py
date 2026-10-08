"""Create (or rebuild) the prepared demo account for the viva (spec section 17).

demo@cinematch.local with about 40 real ratings, so user CF has enough neighbors and every rail shows.
The password is generated once into .env as DEMO_PASSWORD and never printed. Runs through the API,
so ratings, likes and list adds are logged exactly like a real user's.
Run:  .\.venv\Scripts\python.exe -m pipeline.demo_accounts
"""
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from pipeline.common import ROOT, env, get_logger  # noqa: E402

log = get_logger("demo_accounts")
EMAIL = "demo@cinematch.local"

# (title, year, rating 1-10) - well-known films, a clear taste: crime/thrillers and smart sci-fi high,
# broad comedies and horror low. Prisoners, Se7en and Zodiac are left UNRATED for the live demo.
RATINGS = [
    ("The Dark Knight", 2008, 10), ("Inception", 2010, 9), ("Interstellar", 2014, 9), ("Fight Club", 1999, 9),
    ("Gone Girl", 2014, 9), ("The Departed", 2006, 9), ("Shutter Island", 2010, 8), ("Memento", 2000, 10),
    ("The Prestige", 2006, 9), ("No Country for Old Men", 2007, 9), ("Nightcrawler", 2014, 9),
    ("Sicario", 2015, 8), ("Heat", 1995, 9), ("The Silence of the Lambs", 1991, 10), ("Drive", 2011, 8),
    ("Arrival", 2016, 9), ("Blade Runner 2049", 2017, 8), ("Ex Machina", 2015, 8), ("The Matrix", 1999, 9),
    ("Parasite", 2019, 10), ("Oldboy", 2003, 9), ("Memories of Murder", 2003, 9), ("The Usual Suspects", 1995, 9),
    ("L.A. Confidential", 1997, 8), ("Mystic River", 2003, 8), ("Gone Baby Gone", 2007, 8), ("Insomnia", 2002, 7),
    ("Reservoir Dogs", 1992, 8), ("Pulp Fiction", 1994, 9), ("Taxi Driver", 1976, 8), ("Mad Max: Fury Road", 2015, 8),
    ("The Social Network", 2010, 8), ("Whiplash", 2014, 9), ("Joker", 2019, 7),
    ("Grown Ups", 2010, 3), ("Paul Blart: Mall Cop", 2009, 2), ("The Twilight Saga: Breaking Dawn - Part 2", 2012, 2),
    ("Fifty Shades of Grey", 2015, 2), ("Annabelle", 2014, 4), ("Scary Movie 3", 2003, 3),
]
LIKES = [("The Dark Knight", 2008), ("Parasite", 2019), ("Memento", 2000)]
LIST = [("Tenet", 2020), ("Burning", 2018), ("Incendies", 2010)]
ONBOARDING = [("The Dark Knight", 2008), ("Inception", 2010), ("Parasite", 2019), ("Gone Girl", 2014), ("Heat", 1995)]


def ensure_password() -> str:
    pw = env("DEMO_PASSWORD")
    if not pw:
        pw = secrets.token_urlsafe(12)
        with open(ROOT / ".env", "a", encoding="utf-8") as f:
            f.write(f"\nDEMO_PASSWORD={pw}\n")
        log.info("generated DEMO_PASSWORD in .env")
    return pw


def main() -> None:
    from app.db import SessionLocal
    from app.main import app

    pw = ensure_password()
    with SessionLocal() as db:
        db.execute(text("DELETE FROM users WHERE email = :e"), {"e": EMAIL})       # rebuild from scratch
        db.commit()

        def movie(title, year):
            row = db.execute(text("SELECT id FROM movies WHERE title = :t AND year = :y ORDER BY tmdb_vote_count DESC NULLS LAST LIMIT 1"),
                             {"t": title, "y": year}).first()
            return row[0] if row else None

        c = TestClient(app)
        c.post("/api/auth/guest")
        r = c.post("/api/auth/register", json={"email": EMAIL, "password": pw, "display_name": "Demo"})
        assert r.status_code == 200, r.text
        picks = [m for m in (movie(t, y) for t, y in ONBOARDING) if m]
        c.post("/api/onboarding", json={"movie_ids": picks, "languages": ["en", "ko", "hi"],
                                        "liked_genre_ids": [g for (g,) in db.execute(text("SELECT id FROM genres WHERE name IN ('Crime','Thriller','Science Fiction')"))],
                                        "disliked_genre_ids": []})
        missing = []
        for title, year, rating in RATINGS:
            m = movie(title, year)
            if m:
                c.put(f"/api/ratings/{m}", json={"rating": rating})
            else:
                missing.append(title)
        for t, y in LIKES:
            if (m := movie(t, y)):
                c.put(f"/api/reactions/{m}", json={"value": 1})
        for t, y in LIST:
            if (m := movie(t, y)):
                c.put(f"/api/list/{m}")
        me = c.get("/api/me").json()
        home = c.get("/api/recs/home").json()
    log.info("demo account ready: %s ratings, stage %s, rails: %s; not in catalog: %s", me["counts"]["ratings"],
             me["counts"]["stage"], [r["key"].split(":")[0] for r in home["rails"]], missing)


if __name__ == "__main__":
    main()