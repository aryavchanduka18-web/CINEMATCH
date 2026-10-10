"""Filmography rule: who qualifies, and which of their missing films become candidates."""
import pandas as pd

from pipeline.filmographies import missing_films, qualifying_people

CFG = {"lead_max_order": 2, "min_lead_films": 2, "min_director_films": 2, "min_vote_count": 50,
       "min_vote_count_en": 1000, "min_runtime_min": 60}


def test_leading_stars_and_directors_qualify_supporting_actors_do_not():
    credits = pd.DataFrame({
        "tmdb_id": [1, 2, 1, 2, 1, 2],
        "tmdb_person_id": [7, 7, 8, 8, 9, 9],
        "name": ["Star", "Star", "Extra", "Extra", "Director", "Director"],
        "role": ["cast", "cast", "cast", "cast", "director", "director"],
        "credit_order": [0, 1, 9, 12, None, None]})
    assert qualifying_people(credits, CFG)["person_id"].tolist() == [7, 9]


def test_missing_films_use_a_higher_vote_floor_for_english_films():
    people = pd.DataFrame({"person_id": [7], "name": ["Star"]})
    credits = {7: {"cast": [
        {"id": 10, "title": "In catalog", "order": 0, "release_date": "2004-04-30", "vote_count": 400, "original_language": "hi"},
        {"id": 11, "title": "Hindi lead", "order": 0, "release_date": "2004-04-30", "vote_count": 60, "original_language": "hi"},
        {"id": 12, "title": "English lead", "order": 1, "release_date": "2010-01-01", "vote_count": 600, "original_language": "en"},
        {"id": 13, "title": "Cameo", "order": 8, "release_date": "2010-01-01", "vote_count": 9000, "original_language": "en"},
        {"id": 14, "title": "Upcoming", "order": 0, "release_date": "2030-01-01", "vote_count": 0, "original_language": "hi"},
        {"id": 15, "title": "Obscure", "order": 0, "release_date": "1995-01-01", "vote_count": 12, "original_language": "hi"}],
        "crew": [{"id": 16, "title": "Directed", "job": "Director", "release_date": "2012-01-01", "vote_count": 2000,
                  "original_language": "en"}]}}
    m = missing_films(people, credits, in_catalog={10}, cutoff="2026-10-10", cfg=CFG).set_index("tmdb_id")
    assert pd.isna(m.loc[11, "skip_reason"]) and pd.isna(m.loc[16, "skip_reason"])
    assert m.loc[12, "skip_reason"] == "fewer than 1000 votes"
    assert m.loc[14, "skip_reason"] == "not released"
    assert m.loc[15, "skip_reason"] == "fewer than 50 votes"
    assert 13 not in m.index and 10 not in m.index          # cameos are not leads; catalog films are skipped
