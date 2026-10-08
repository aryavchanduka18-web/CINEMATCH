"""The catalog loader (pipeline step 12) is idempotent and fills the search vector."""
import pandas as pd
from sqlalchemy import text

from pipeline.catalog import parse_credits, parse_movie
from pipeline.loader import load_catalog
from pipeline.tests.fixtures import good


def _frames():
    details = [good(id=900001), good(id=900002, title="Second Film", imdb_id="tt0900002")]
    movies = pd.DataFrame([parse_movie(d) for d in details])
    movies["catalog_part"] = ["A", "B"]
    movies["ml_movie_id"] = pd.array([555001, None], dtype="Int64")
    movies["dominant_color"] = "#336699"
    credits = pd.DataFrame([r for d in details for r in parse_credits(d)])
    awards = pd.DataFrame([{"tmdb_id": 900001, "award": "Academy Awards", "category": "Best Picture",
                            "year": 1996, "result": "won", "wikidata_id": "Q1"}])
    aggregates = pd.DataFrame([{"ml_movie_id": 555001, "ml_rating_count": 3, "ml_rating_mean": 8.0,
                                "rating_hist": [0, 0, 0, 0, 0, 0, 1, 1, 1, 0]}])
    return movies, credits, awards, aggregates


def test_loader_is_idempotent(test_engine):
    frames = _frames()
    first = load_catalog(test_engine, *frames)
    second = load_catalog(test_engine, *frames)
    assert first == second
    with test_engine.connect() as conn:
        dupes = conn.execute(text("select count(*) - count(distinct tmdb_id) from movies")).scalar()
        row = conn.execute(text(
            "select ml_rating_count, ml_rating_mean, rating_hist, dominant_color from movies where tmdb_id = 900001")).one()
        n_credits = conn.execute(text(
            "select count(*) from movie_credits mc join movies m on m.id = mc.movie_id where m.tmdb_id = 900001")).scalar()
    assert dupes == 0
    assert row.ml_rating_count == 3 and float(row.ml_rating_mean) == 8.0 and row.rating_hist[6] == 1
    assert row.dominant_color == "#336699"
    assert n_credits == 17                                    # 15 cast + 1 director + 1 writer


def test_search_vector_has_title_cast_and_director(test_engine):
    load_catalog(test_engine, *_frames())
    with test_engine.connect() as conn:
        def hits(q):
            return conn.execute(text(
                "select count(*) from movies where tmdb_id = 900001 and search_vector @@ plainto_tsquery('simple', :q)"),
                {"q": q}).scalar()
        assert hits("test film") == 1
        assert hits("dir one") == 1          # director
        assert hits("actor 3") == 1          # cast

def test_loader_prunes_stale_films_but_keeps_ones_users_reference(test_engine):
    movies, credits, awards, aggregates = _frames()
    load_catalog(test_engine, movies, credits, awards, aggregates)
    with test_engine.begin() as conn:
        rated = conn.execute(text("select id from movies where tmdb_id = 900002")).scalar()
        uid = conn.execute(text("insert into users (display_name) values ('p') returning id")).scalar()
        conn.execute(text("insert into ratings (user_id, movie_id, rating) values (:u, :m, 9)"), {"u": uid, "m": rated})
    # Catalog shrinks to nothing: 900001 is unreferenced and goes; 900002 has a rating and stays.
    counts = load_catalog(test_engine, movies.iloc[0:0], credits.iloc[0:0], awards.iloc[0:0], aggregates)
    with test_engine.begin() as conn:
        left = {r[0] for r in conn.execute(text("select tmdb_id from movies where tmdb_id in (900001, 900002)"))}
        conn.execute(text("delete from users where id = :u"), {"u": uid})
    assert left == {900002}
    assert counts["stale_movies_kept_for_user_data"] >= 1