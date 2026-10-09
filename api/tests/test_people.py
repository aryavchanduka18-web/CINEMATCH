"""Cast and crew pages: person summary, filmography with roles and characters, 404s."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app


@pytest.fixture(scope="module")
def person(test_engine):
    with test_engine.begin() as conn:
        a = conn.execute(text("INSERT INTO movies (tmdb_id, title, year, release_date, tmdb_vote_count) VALUES (950001, 'Old Film', 1997, '1997-12-05', 9000) RETURNING id")).scalar()
        b = conn.execute(text("INSERT INTO movies (tmdb_id, title, year, release_date, tmdb_vote_count) VALUES (950002, 'New Film', 2015, '2015-10-02', 5000) RETURNING id")).scalar()
        pid = conn.execute(text("INSERT INTO people (tmdb_person_id, name, profile_path) VALUES (950900, 'Matt Example', '/m.jpg') RETURNING id")).scalar()
        conn.execute(text("INSERT INTO movie_credits (movie_id, person_id, role, character, credit_order) VALUES "
                          "(:a, :p, 'cast', 'Will', 0), (:a, :p, 'writer', NULL, NULL), (:b, :p, 'cast', 'Mark', 0)"),
                     {"a": a, "b": b, "p": pid})
    yield pid
    with test_engine.begin() as conn:
        conn.execute(text("DELETE FROM movies WHERE tmdb_id IN (950001, 950002)"))
        conn.execute(text("DELETE FROM people WHERE tmdb_person_id = 950900"))


def test_person_summary(person):
    p = TestClient(app).get(f"/api/people/{person}").json()
    assert p["name"] == "Matt Example" and p["known_for"] == "Acting" and p["film_count"] == 2
    assert p["departments"] == {"Acting": 2, "Writing": 1}
    assert p["known_for_titles"][0]["title"] == "Old Film"


def test_filmography_newest_first_with_roles_and_characters(person):
    res = TestClient(app).get(f"/api/people/{person}/movies").json()
    items = res["items"]
    assert [i["movie"]["title"] for i in items] == ["New Film", "Old Film"]
    assert items[1]["roles"] == ["Acting", "Writing"] and items[1]["character"] == "Will"
    assert res["recommended"] == []        # a new visitor has no Match % yet: nothing is invented


def test_unknown_person_is_404():
    c = TestClient(app)
    assert c.get("/api/people/999999999").status_code == 404
    assert c.get("/api/people/999999999/movies").status_code == 404
