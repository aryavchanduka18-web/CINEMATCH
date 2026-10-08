"""Baseline models and the evaluation protocol on a tiny hand-made dataset."""
import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from cinematch_engine.data.splits import build_split
from cinematch_engine.eval.protocol import rank_users, sample_eval_users, top_k
from cinematch_engine.models.bias import BiasBaseline
from cinematch_engine.models.item_cf import ItemCF
from cinematch_engine.models.popularity import PopularityModel, bayesian_average
from cinematch_engine.models.user_cf import UserCF

# 4 users x 5 films (0 = not rated)
R = np.array([
    [9, 8, 0, 2, 0],
    [8, 9, 3, 0, 7],
    [2, 0, 9, 8, 0],
    [9, 7, 2, 0, 8],
], dtype=np.float32)


def _split():
    rows = [{"user_id": u + 1, "ml_movie_id": i + 1, "rating": R[u, i]} for u, i in zip(*np.nonzero(R))]
    held = [{"user_id": 1, "ml_movie_id": 5, "rating": 8}, {"user_id": 3, "ml_movie_id": 2, "rating": 3},
            {"user_id": 4, "ml_movie_id": 4, "rating": 9}]
    items = pd.DataFrame({"ml_movie_id": range(1, 6), "tmdb_id": range(101, 106)})
    return build_split(pd.DataFrame(rows), pd.DataFrame(held), items, "val")


def test_bayesian_average_by_hand():
    # one film rated twice with mean 10, m = 2, global mean 6 -> 0.5 * 10 + 0.5 * 6 = 8
    assert bayesian_average(np.array([20.0]), np.array([2]), 6.0, 2.0)[0] == pytest.approx(8.0)
    assert bayesian_average(np.array([0.0]), np.array([0]), 6.0, 2.0)[0] == pytest.approx(6.0)


def test_rankings_never_contain_training_films():
    data = _split()
    pop = PopularityModel(m=1).fit(data.train)
    recs = rank_users(pop.score, data, np.arange(data.n_users), k=1)
    for u, lst in enumerate(recs):
        assert not set(lst) & set(np.nonzero(R[u])[0])
    scores = np.ones((1, 5), dtype=np.float32)
    assert set(top_k(scores, [np.array([0, 1, 2])], 2)[0]) == {3, 4}


def test_eval_user_sample_is_fixed_and_model_independent():
    data = _split()
    a, b = sample_eval_users(data, n=2, seed=42), sample_eval_users(data, n=2, seed=42)
    assert (a == b).all()
    # only users with a relevant (>= 7) held-out film are eligible: users 1 and 4 -> indices 0 and 3
    assert set(sample_eval_users(data, n=10, seed=42)) == {0, 3}


def _adjusted_cosine_brute(R, means, i, j):
    co = (R[:, i] > 0) & (R[:, j] > 0)
    a, b = R[co, i] - means[co], R[co, j] - means[co]
    return float(a @ b / np.sqrt((a @ a) * (b @ b))) if co.any() else 0.0


def test_item_cf_matches_brute_force_adjusted_cosine():
    data = _split()
    means = data.user_means()
    m = ItemCF(shrinkages=(0,), max_neighbors=4, block=2).fit(data.train, means).configure(0, 4)
    sim = m.sim.toarray()
    for i in range(5):
        for j in range(5):
            if i != j and sim[i, j] > 0:
                assert sim[i, j] == pytest.approx(_adjusted_cosine_brute(R, means, i, j), abs=1e-5)
    assert sim[0, 1] > 0                     # films 0 and 1 are liked together


def test_user_cf_significance_weighting_and_prediction():
    data = _split()
    means = data.user_means()
    m = UserCF(max_neighbors=3).fit(data.train, means)
    corr, n = m.similarities(np.array([0]))
    idx, vals = m.neighbors(np.array([0]), min_overlap=1, cached=(corr, n))
    # users 0 and 3 share 2 films: weight = pearson * 2/50
    assert n[0, 3] == 2
    v3 = vals[0][list(idx[0]).index(3)]
    assert v3 == pytest.approx(corr[0, 3] * 2 / 50, abs=1e-6)
    # overlap filter removes every pair below the minimum
    _, vals_strict = m.neighbors(np.array([0]), min_overlap=3, cached=(corr, n))
    assert (vals_strict == 0).all()


def test_bias_baseline_learns_user_and_film_offsets():
    data = _split()
    b = BiasBaseline(reg_item=0.0, reg_user=0.0, iterations=10).fit(data.train)
    # Film 0 averages 7.0, film 2 averages 4.67: same user, film 0 predicted higher.
    pred = b.predict(np.array([0, 0]), np.array([0, 2]))
    assert pred[0] > pred[1]
    # User 1 rates higher on average (6.75) than user 0 (6.33): same film, user 1 predicted higher.
    pred = b.predict(np.array([1, 0]), np.array([4, 4]))
    assert pred[0] > pred[1]