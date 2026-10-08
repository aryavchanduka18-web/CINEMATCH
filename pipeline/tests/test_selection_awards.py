from datetime import date

import pandas as pd

from pipeline.catalog import backbone_ml_ids
from pipeline.selection import (boost_floor, hollywood_pick, hollywood_rule, pick_part_c_threshold, pick_threshold,
                                relaxed_additions, select)

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

def test_boost_floor_is_the_highest_floor_reaching_target():
    votes = pd.Series(range(1, 201))          # one film per vote count 1..200
    # Enough films already at the normal floor: no lowering needed.
    assert boost_floor(votes, already=20, target=150, start=50, floor=5, cap=300) == 50
    # Pool too small even at the floor: stop at the floor.
    assert boost_floor(votes.head(60), already=20, target=150, start=50, floor=5, cap=300) == 5
    # 100 already + 10 well-voted films; 40 more are needed, reached by lowering to 10 votes.
    assert boost_floor(pd.Series([100] * 10 + list(range(5, 50))), already=100, target=150,
                       start=50, floor=5, cap=300) == 10

H = {"min_vote_count": 2000, "classic_before_year": 1990, "classic_min_vote_count": 1000,
     "collection_min_vote_count": 1000}


def _d(tmdb_id, votes, year, coll=False, us=True, status="Released", date_="2010-01-01"):
    return {"tmdb_id": tmdb_id, "tmdb_vote_count": votes, "year": year, "in_collection": coll,
            "us_production": us, "status": status, "release_date": date_}


def test_hollywood_rule_votes_classics_and_franchises():
    df = pd.DataFrame([_d(1, 2500, 2010), _d(2, 1500, 1985), _d(3, 1500, 2010, coll=True),
                       _d(4, 1500, 2010), _d(5, 999, 1980)])
    assert hollywood_rule(df, H).tolist() == [True, True, True, False, False]


def test_hollywood_pick_needs_us_release_and_skips_existing():
    df = pd.DataFrame([_d(1, 5000, 2010), _d(2, 5000, 2010, us=False), _d(3, 5000, 2026, status="Post Production"),
                       _d(4, 5000, 2010), _d(5, 5000, 2027, date_="2027-01-01")])
    picked = hollywood_pick(df, H, date(2026, 10, 8), exclude={4})
    assert picked["tmdb_id"].tolist() == [1]


def test_relaxed_additions_use_frozen_settings_and_leave_the_base_alone():
    def row(tmdb_id, part, original, ml=None, votes=0, lang=None):
        return {"tmdb_id": tmdb_id, "part": part, "ml_rating_count": ml, "tmdb_vote_count": votes,
                "discover_language": lang, "release_date": "2000-01-01", "status": "Released",
                "passed": True, "original_passed": original}
    gated = pd.DataFrame([row(i, "A", True, ml=100 + i) for i in range(10)]          # backbone
                         + [row(50, "A", False, ml=200), row(51, "A", False, ml=60)]  # relaxed-only A
                         + [row(60 + i, "B", True, votes=100 + i, lang="hi") for i in range(3)]
                         + [row(70, "B", False, votes=500, lang="hi"), row(71, "B", False, votes=50, lang="hi")])
    cfg = {"part_a": {"target": 5, "min_ratings": 50}, "part_b": {"max_per_language": 3},
           "part_c": {"start_min_votes": 100, "target_min": 0, "target_max": 500, "pool_min_votes": 50}}
    start, end = date(2025, 1, 1), date(2026, 1, 1)
    base, chosen = select(gated.assign(passed=gated["original_passed"]), cfg, start, end)
    extra = relaxed_additions(gated, base, chosen, cfg, start, end)
    assert chosen["part_a_min_ratings"] == 105                  # 5 backbone films: 105..109
    assert sorted(extra["tmdb_id"]) == [50, 70]                 # 51 is below the A threshold, 71 below the B cut
    assert not set(extra["tmdb_id"]) & set(base["tmdb_id"])


def test_backbone_excludes_films_added_by_the_relaxed_gate():
    catalog = pd.DataFrame({"catalog_part": ["A", "A", "B"], "ml_movie_id": [1, 2, None],
                            "relaxed_gate": [False, True, False]})
    assert backbone_ml_ids(catalog).tolist() == [1]
    assert backbone_ml_ids(catalog.drop(columns="relaxed_gate")).tolist() == [1, 2]   # older catalog files
