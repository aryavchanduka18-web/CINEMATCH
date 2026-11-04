"""Public launch: keep-awake ping, traffic limits, housekeeping, rating import and the owner's stats page."""
import uuid

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import get_settings
from app.main import app
from app.ratelimit import GUEST
from app.routers.imports import normalize, parse
from app.services import cleanup
from pipeline.catalog import parse_credits, parse_movie
from pipeline.loader import load_catalog
from pipeline.tests.fixtures import good

# (tmdb id, title, year, imdb id)
FILMS = [(920001, "Andhadhun", 2018, "tt8108198"), (920002, "Dil Chahta Hai", 2001, "tt0292490"),
         (920003, "The Prestige", 2006, "tt0482571"), (920004, "Spider-Man: No Way Home", 2021, "tt10872600")]


@pytest.fixture(scope="module")
def catalog(test_engine):
    details = [good(id=t, title=title, original_title=title, imdb_id=imdb, release_date=f"{y}-06-01",
                    vote_count=3000, credits={"cast": [], "crew": []}) for t, title, y, imdb in FILMS]
    movies = pd.DataFrame([parse_movie(d) for d in details])
    movies["catalog_part"] = "B"
    movies["ml_movie_id"] = pd.array([None] * len(movies), dtype="Int64")
    movies["dominant_color"] = "#336699"
    credits = pd.DataFrame([r for d in details for r in parse_credits(d)],
                           columns=["tmdb_id", "tmdb_person_id", "name", "profile_path", "role", "character", "credit_order"])
    load_catalog(test_engine, movies, credits, pd.DataFrame(columns=["tmdb_id"]), pd.DataFrame(), prune=False)
    with test_engine.connect() as c:
        return dict(c.execute(text("SELECT tmdb_id, id FROM movies WHERE tmdb_id = ANY(:t)"),
                              {"t": [f[0] for f in FILMS]}).all())


def signed_in(email: str | None = None) -> TestClient:
    c = TestClient(app)
    res = c.post("/api/auth/register", json={"email": email or f"u{uuid.uuid4().hex[:10]}@example.com",
                                             "password": "popcorn42night"})
    assert res.status_code == 200
    return c


# ---------------------------------------------------------------- keep-awake ping

def test_ping_answers_without_the_database():
    from app.db import get_db

    def broken():
        raise AssertionError("ping must not open a database session")
        yield
    app.dependency_overrides[get_db] = broken
    try:
        assert TestClient(app).get("/api/ping").json() == {"status": "ok"}
    finally:
        app.dependency_overrides.pop(get_db)


# ---------------------------------------------------------------- traffic limits

def test_guest_sessions_are_limited_per_address():
    c = TestClient(app)
    for _ in range(GUEST.max_failures):
        assert c.post("/api/auth/guest").status_code == 200
    res = c.post("/api/auth/guest")
    assert res.status_code == 429 and "Try again" in res.json()["detail"]


def test_events_beyond_the_budget_are_dropped_not_stored(test_engine):
    c = TestClient(app)
    uid = c.post("/api/auth/guest").json()["id"]
    results = [c.post("/api/events", json={"event_type": "quick_view"}).json() for _ in range(125)]
    assert sum(1 for r in results if r.get("dropped")) == 5
    with test_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM interactions WHERE user_id = :u"), {"u": uid}).scalar() == 120


# ---------------------------------------------------------------- housekeeping

def test_cleanup_deletes_idle_guests_and_old_logs_only(test_engine, catalog):
    mid = next(iter(catalog.values()))
    with test_engine.begin() as c:
        ins = "INSERT INTO users (is_guest, email, created_at) VALUES (:g, :e, now() - make_interval(days => :d)) RETURNING id"
        idle = c.execute(text(ins), {"g": True, "e": None, "d": 40}).scalar()
        busy = c.execute(text(ins), {"g": True, "e": None, "d": 40}).scalar()
        young = c.execute(text(ins), {"g": True, "e": None, "d": 5}).scalar()
        member = c.execute(text(ins), {"g": False, "e": f"old{uuid.uuid4().hex[:8]}@example.com", "d": 400}).scalar()
        c.execute(text("INSERT INTO interactions (user_id, movie_id, event_type) VALUES (:u, :m, 'detail_view')"),
                  {"u": busy, "m": mid})
        for days in (90, 1):
            c.execute(text("""INSERT INTO recommendation_logs (user_id, movie_id, created_at)
                              VALUES (:u, :m, now() - make_interval(days => :d))"""), {"u": member, "m": mid, "d": days})
    from app.db import SessionLocal
    with SessionLocal() as db:
        result = cleanup.run(db)
    assert result["guests_deleted"] >= 1 and result["logs_deleted"] >= 1
    with test_engine.connect() as c:
        left = {r[0] for r in c.execute(text("SELECT id FROM users WHERE id = ANY(:ids)"),
                                        {"ids": [idle, busy, young, member]})}
        logs = c.execute(text("SELECT count(*) FROM recommendation_logs WHERE user_id = :u"), {"u": member}).scalar()
    assert left == {busy, young, member}
    assert logs == 1


# ---------------------------------------------------------------- import

LETTERBOXD = """Date,Name,Year,Letterboxd URI,Rating
2024-01-02,Andhadhun,2018,https://boxd.it/a,4.5
2024-01-03,Dil Chahta Hai,2002,https://boxd.it/b,5
2024-01-04,Spider-Man: No Way Home,2021,https://boxd.it/c,3
2024-01-05,A Film We Do Not Have,1999,https://boxd.it/d,2
2024-01-06,The Prestige,1990,https://boxd.it/e,4
"""

IMDB = """﻿Const,Your Rating,Date Rated,Title,Original Title,URL,Title Type,IMDb Rating,Runtime (mins),Year,Genres,Num Votes,Release Date,Directors
tt0482571,9,2024-01-01,The Prestige,The Prestige,https://imdb.com/x,Movie,8.5,130,2006,Drama,1,2006-10-20,Nolan
tt0903747,10,2024-01-01,Breaking Bad,Breaking Bad,https://imdb.com/y,TV Series,9.5,49,2008,Drama,1,2008-01-20,
tt9999999,7,2024-01-01,Unknown,Unknown,https://imdb.com/z,Movie,6.0,90,2010,Drama,1,2010-01-01,
"""


def test_normalize_matches_the_database_rule():
    assert normalize("Spider-Man: No Way Home") == "spider man no way home"
    assert normalize("L.A. Confidential") == "la confidential"


def test_parse_detects_the_format_and_converts_stars():
    kind, rows = parse(LETTERBOXD)
    assert kind == "letterboxd" and [r["rating"] for r in rows] == [9, 10, 6, 4, 8]
    kind, rows = parse(IMDB)
    assert kind == "imdb" and [r["imdb"] for r in rows] == ["tt0482571", "tt9999999"]    # TV series skipped


def test_letterboxd_import_matches_title_and_year(test_engine, catalog):
    c = signed_in()
    res = c.post("/api/me/import", json={"csv": LETTERBOXD})
    assert res.status_code == 200, res.text
    body = res.json()
    # Andhadhun, Dil Chahta Hai (one year off is fine), Spider-Man; not the unknown film, not The Prestige (1990 != 2006)
    assert body["imported"] == 3 and body["not_found"] == 2
    assert "A Film We Do Not Have" in body["not_found_examples"]
    uid = c.get("/api/me").json()["id"]
    with test_engine.connect() as conn:
        got = dict(conn.execute(text("SELECT movie_id, rating FROM ratings WHERE user_id = :u"), {"u": uid}).all())
    assert got == {catalog[920001]: 9, catalog[920002]: 10, catalog[920004]: 6}


def test_imdb_import_matches_ids_and_keeps_existing_ratings(test_engine, catalog):
    c = signed_in()
    assert c.put(f"/api/ratings/{catalog[920003]}", json={"rating": 4}).status_code == 200
    body = c.post("/api/me/import", json={"csv": IMDB}).json()
    assert body["imported"] == 0 and body["already_rated"] == 1 and body["not_found"] == 1
    uid = c.get("/api/me").json()["id"]
    with test_engine.connect() as conn:
        assert conn.execute(text("SELECT rating FROM ratings WHERE user_id = :u AND movie_id = :m"),
                            {"u": uid, "m": catalog[920003]}).scalar() == 4


def test_import_rejects_other_files():
    c = signed_in()
    assert c.post("/api/me/import", json={"csv": "a,b\n1,2\n"}).status_code == 422
    res = c.post("/api/me/import", json={"csv": "Date,Name,Year,Letterboxd URI\n2024-01-01,X,2000,u\n"})
    assert res.status_code == 422 and "ratings.csv" in res.json()["detail"]


# ---------------------------------------------------------------- owner's stats

def test_stats_are_only_for_admin_emails(monkeypatch):
    admin_email = f"owner{uuid.uuid4().hex[:8]}@example.com"
    monkeypatch.setattr(get_settings(), "admin_emails", f"someone@else.com, {admin_email.upper()}")
    assert TestClient(app).get("/api/admin/stats").status_code in (401, 404)
    assert signed_in().get("/api/admin/stats").status_code == 404
    res = signed_in(admin_email).get("/api/admin/stats")
    assert res.status_code == 200
    body = res.json()
    assert body["accounts"] >= 1 and len(body["daily"]) == 30 and body["database_bytes"] > 0
