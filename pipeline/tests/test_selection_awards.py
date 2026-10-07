from datetime import date

import pandas as pd

from pipeline.selection import pick_part_c_threshold, pick_threshold, select

award_mod = __import__("importlib").import_module("pipeline.04_fetch_awards_wikidata")


def test_pick_threshold_lands_near_target():
    counts = pd.Series(range(1, 1001))           # film i has i ratings
    t = pick_threshold(counts, target=300, floor=50)
    assert (counts >= t).sum() == 300


def test_part_c_threshold_moves_into_range():
    votes = pd.Series(range(50, 2050))           # 2000 films
    t = pick_part_c_threshold(votes, start=100, lo=300, hi=500, floor=50)
    assert 300 <= (votes >= t).sum() <= 500


def test_select_dedupes_parts_and_caps_languages():
    rows = [{"tmdb_id": i, "part": "A", "ml_rating_count": 100 + i, "tmdb_vote_count": 0,
             "discover_language": None, "release_date": "2000-01-01", "status": "Released", "passed": True}
            for i in range(10)]
    rows += [{"tmdb_id": 5, "part": "B", "ml_rating_count": None, "tmdb_vote_count": 999,
              "discover_language": "hi", "release_date": "2000-01-01", "status": "Released", "passed": True}]
    rows += [{"tmdb_id": 100 + i, "part": "B", "ml_rating_count": None, "tmdb_vote_count": i,
              "discover_language": "hi", "release_date": "2000-01-01", "status": "Released", "passed": True}
             for i in range(5)]
    cfg = {"part_a": {"target": 10, "min_ratings": 50}, "part_b": {"max_per_language": 3},
           "part_c": {"start_min_votes": 100, "target_min": 0, "target_max": 500, "pool_min_votes": 50}}
    cat, _ = select(pd.DataFrame(rows), cfg, date(2025, 1, 1), date(2026, 1, 1))
    assert cat["tmdb_id"].is_unique
    assert (cat["part"] == "B").sum() == 3                     # language cap
    assert cat.loc[cat.tmdb_id == 5, "part"].item() == "A"     # A wins over B


def test_split_prize_names():
    known = {"Academy Awards"}
    assert award_mod.split_prize("Academy Award for Best Actor", None, known) == ("Academy Awards", "Best Actor")
    assert award_mod.split_prize("Palme d'Or", None, known) == ("Palme d'Or", None)
    assert award_mod.split_prize("Saturn Award for Best Costume", "Saturn Awards", known) == ("Saturn Awards", "Best Costume")