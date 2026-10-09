"""Themed collections: membership from real genres, pinned titles first, small collections hidden."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app

FILMS = [  # tmdb, title, year, genres, votes
    (940001, "Leap Year", 2010, ["Romance", "Comedy"], 2000), (940002, "Big Romcom", 2015, ["Romance", "Comedy"], 9000),
    (940003, "Only Romance", 2001, ["Romance"], 5000), (940004, "Romcom Three", 2003, ["Romance", "Comedy"], 100),
    (940005, "Romcom Four", 2004, ["Comedy", "Romance"], 50), (940006, "Romcom Five", 2005, ["Romance", "Comedy"], 40),
    (940007, "Romcom Six", 2006, ["Romance", "Comedy"], 30),
]


@pytest.fixture(scope="module")
def films(test_engine):
    with test_engine.begin() as conn:
        for t, title, year, genres, votes in FILMS:
            mid = conn.execute(text("""INSERT INTO movies (tmdb_id, title, year, tmdb_vote_count, popularity_score)
                VALUES (:t, :ti, :y, :v, :v) RETURNING id"""), {"t": t, "ti": title, "y": year, "v": votes}).scalar()
            for g in genres:
                gid = conn.execute(text("""INSERT INTO genres (name, slug) VALUES (:g, lower(:g))
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id"""), {"g": g}).scalar()
                conn.execute(text("INSERT INTO movie_genres (movie_id, genre_id) VALUES (:m, :g)"), {"m": mid, "g": gid})
    yield
    with test_engine.begin() as conn:
        conn.execute(text("DELETE FROM movies WHERE tmdb_id BETWEEN 940000 AND 940999"))


def test_rom_com_pins_leap_year_then_orders_by_popularity(films):
    res = TestClient(app).get("/api/collections")
    rom = next(c for c in res.json()["collections"] if c["key"] == "rom-com")
    titles = [i["movie"]["title"] for i in rom["items"]]
    assert titles[0] == "Leap Year"
    assert titles[1] == "Big Romcom"
    assert "Only Romance" not in titles
    assert rom["count"] == 6


def test_collections_under_six_films_are_hidden(films):
    keys = {c["key"] for c in TestClient(app).get("/api/collections").json()["collections"]}
    assert "crime-thriller" not in keys


def test_collection_page_and_unknown_key(films):
    c = TestClient(app)
    assert c.get("/api/collections/rom-com").json()["count"] == 6
    assert c.get("/api/collections/nope").status_code == 404
