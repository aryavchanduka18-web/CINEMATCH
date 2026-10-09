"""Franchise rule: which missing collection parts become candidates, and stage-ordered label columns."""
import numpy as np
import pandas as pd

from cinematch_engine.models.content import build_blocks, combine
from pipeline.franchises import missing_parts


def test_missing_parts_keeps_released_known_films_only():
    col = {1: {"name": "Wick Collection", "parts": [
        {"id": 10, "title": "One", "release_date": "2014-10-24", "vote_count": 20000},
        {"id": 11, "title": "Two", "release_date": "2017-02-10", "vote_count": 15000},
        {"id": 12, "title": "Five", "release_date": "2030-01-01", "vote_count": 0},
        {"id": 13, "title": "Clip", "release_date": "2015-01-01", "vote_count": 12},
        {"id": 14, "title": "X", "release_date": "2015-01-01", "vote_count": 900, "adult": True}]}}
    m = missing_parts(col, in_catalog={10}, cutoff="2026-10-08", min_votes=200).set_index("tmdb_id")
    assert pd.isna(m.loc[11, "skip_reason"])
    assert m.loc[12, "skip_reason"] == "not released"
    assert m.loc[13, "skip_reason"] == "fewer than 200 votes"
    assert m.loc[14, "skip_reason"] == "adult"
    assert 10 not in m.index


def _movies(names: list[list[str]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    n = len(names)
    movies = pd.DataFrame({"tmdb_id": range(n), "overview": [f"story {w} adventure" for w in ("red", "blue", "green", "gold")[:n]], "keywords": [[]] * n,
                           "tagline": [None] * n, "genres": [["Drama"]] * n, "original_language": ["en"] * n,
                           "countries": [["US"]] * n, "studios": names})
    return movies, pd.DataFrame(columns=["tmdb_id", "role", "name", "credit_order"])


def test_label_columns_of_an_earlier_stage_keep_their_positions():
    """Adding a later stage (franchise films) must not move the extra columns of an earlier stage."""
    names = [["Alpha"], ["Beta"], ["Zeta"], ["Gamma"]]
    fit = np.array([True, True, False, False])
    movies, credits = _movies(names)
    two = combine(build_blocks(movies.iloc[:3], credits, ngram_max=1, fit_mask=fit[:3], stage=np.array([0, 0, 1])))
    three = combine(build_blocks(movies, credits, ngram_max=1, fit_mask=fit, stage=np.array([0, 0, 1, 2])))
    old = three.matrix[:3][:, three.columns_up_to(1)].toarray()
    assert np.array_equal(old, two.matrix.toarray())
    later = np.setdiff1d(np.arange(three.matrix.shape[1]), three.columns_up_to(1))
    assert three.matrix[:3][:, later].nnz == 0
