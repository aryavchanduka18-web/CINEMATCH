"""Monthly new releases: candidates accumulate, catalog films are skipped (pipeline/new_releases.py)."""
from datetime import date

import pandas as pd

from pipeline.new_releases import COLUMNS, merge, min_votes, months_back


def test_months_back_handles_year_ends_and_short_months():
    assert months_back(date(2026, 11, 4), 6) == date(2026, 5, 4)
    assert months_back(date(2026, 3, 31), 6) == date(2025, 9, 28)


def test_low_volume_languages_have_a_lower_floor():
    assert min_votes("kn") < min_votes("hi") == min_votes("en")


def test_merge_keeps_earlier_candidates_and_skips_catalog_films():
    old = pd.DataFrame([{"tmdb_id": 1, "tmdb_vote_count": 300, "discover_language": "hi", "found_on": "2026-10-01", "part": "C"}],
                       columns=COLUMNS)
    found = pd.DataFrame({"tmdb_id": [1, 2, 3], "tmdb_vote_count": [900, 150, 120], "discover_language": ["hi", "en", "ta"]})
    out = merge(old, found, in_catalog={3}, today=date(2026, 11, 4))
    assert out["tmdb_id"].tolist() == [1, 2]
    assert out.set_index("tmdb_id").loc[1, "found_on"] == "2026-10-01"    # first sighting kept as it was
    assert out.set_index("tmdb_id").loc[2, "found_on"] == "2026-11-04"
