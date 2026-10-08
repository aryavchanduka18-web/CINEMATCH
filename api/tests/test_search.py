"""Search tolerates punctuation and typos in titles (normalized title + pg_trgm, migration 0004)."""
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from pipeline.catalog import parse_credits, parse_movie
from pipeline.loader import load_catalog
from pipeline.tests.fixtures import good

# (tmdb id, title, votes): the four target films plus look-alike decoys.
FILMS = [
    (910001, "L.A. Confidential", 4000), (910002, "Spenser Confidential", 2500),
    (910003, "How to Lose a Guy in 10 Days", 3500), (910004, "How to Train Your Dragon", 9000),
    (910005, "Horrible Bosses", 6000), (910006, "Horrible Bosses 2", 4000), (910007, "Bad Bosses", 100),
    (910008, "Central Intelligence", 5500), (910009, "Central Station", 800),
    (910010, "The Godfather", 20000), (910011, "Godfather", 50),
]


@pytest.fixture(scope="module")
def client(test_engine):
    details = [good(id=t, title=title, original_title=title, imdb_id=f"tt{t}", vote_count=v,
                    credits={"cast": [], "crew": []}) for t, title, v in FILMS]
    movies = pd.DataFrame([parse_movie(d) for d in details])
    movies["catalog_part"] = "B"
    movies["ml_movie_id"] = pd.array([None] * len(movies), dtype="Int64")
    movies["dominant_color"] = "#336699"
    credits = pd.DataFrame([r for d in details for r in parse_credits(d)],
                           columns=["tmdb_id", "tmdb_person_id", "name", "profile_path", "role", "character", "credit_order"])
    load_catalog(test_engine, movies, credits, pd.DataFrame(columns=["tmdb_id"]), pd.DataFrame(), prune=False)
    with TestClient(app) as c:
        yield c


def titles(client, q: str) -> list[str]:
    res = client.get("/api/search", params={"q": q})
    assert res.status_code == 200
    return [i["movie"]["title"] for i in res.json()["items"]]


@pytest.mark.parametrize("query, expected", [
    ("LA confidential", "L.A. Confidential"),                 # punctuation in the stored title
    ("how to loose a guy", "How to Lose a Guy in 10 Days"),  # misspelled word
    ("horrible bossses", "Horrible Bosses"),                 # repeated letter
    ("central intellgence", "Central Intelligence"),         # dropped letter
])
def test_typo_and_punctuation_queries_find_the_film_first(client, query, expected):
    assert titles(client, query)[0] == expected


def test_exact_title_ranks_above_less_known_namesakes(client):
    assert titles(client, "godfather")[:2] == ["The Godfather", "Godfather"]


def test_no_false_positives(client):
    assert titles(client, "xqzvt wplkj") == []
    # A different film that shares a word is not returned as a typo match.
    assert "How to Train Your Dragon" not in titles(client, "how to loose a guy")
    assert "Central Station" not in titles(client, "central intellgence")
    assert "Bad Bosses" not in titles(client, "horrible bossses")
