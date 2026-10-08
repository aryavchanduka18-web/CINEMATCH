"""Every metric checked against a value worked out by hand."""
import math

import numpy as np
import pytest

from cinematch_engine.eval import metrics as M

RECS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
REL = {2, 5, 11}          # hits at positions 2 and 5; film 11 is relevant but not recommended


def test_precision_and_recall():
    assert M.precision_at_k(RECS, REL, 10) == pytest.approx(2 / 10)
    assert M.precision_at_k(RECS, REL, 5) == pytest.approx(2 / 5)
    assert M.recall_at_k(RECS, REL, 10) == pytest.approx(2 / 3)


def test_average_precision():
    # (P@2 + P@5) / min(|rel|, k) = (1/2 + 2/5) / 3 = 0.3
    assert M.average_precision_at_k(RECS, REL, 10) == pytest.approx(0.3)
    assert M.average_precision_at_k([2, 5, 11], REL, 10) == pytest.approx(1.0)


def test_ndcg():
    dcg = 1 / math.log2(3) + 1 / math.log2(6)                    # hits at positions 2 and 5
    idcg = 1 + 1 / math.log2(3) + 1 / math.log2(4)              # 3 relevant films at the top
    assert M.ndcg_at_k(RECS, REL, 10) == pytest.approx(dcg / idcg)
    assert M.ndcg_at_k(RECS, REL, 10) == pytest.approx(0.47762, abs=1e-5)
    assert M.ndcg_at_k([2, 5, 11], REL, 10) == pytest.approx(1.0)


def test_empty_relevant_set_scores_zero():
    for f in (M.precision_at_k, M.recall_at_k, M.average_precision_at_k, M.ndcg_at_k):
        assert f(RECS, set(), 10) == 0.0


def test_rmse_and_mae():
    # errors 1, 0, -2 -> MSE 5/3
    assert M.rmse([3, 4, 5], [2, 4, 7]) == pytest.approx(math.sqrt(5 / 3))
    assert M.mae([3, 4, 5], [2, 4, 7]) == pytest.approx(1.0)


def test_diversity_and_novelty():
    sim = np.array([[1.0, 0.5, 0.0], [0.5, 1.0, 0.2], [0.0, 0.2, 1.0]])
    # mean off-diagonal similarity = (0.5 + 0.0 + 0.2) / 3
    assert M.intra_list_diversity([0, 1, 2], sim) == pytest.approx(1 - 0.7 / 3)
    share = np.array([0.5, 0.25, 0.125])
    assert M.novelty([0, 1, 2], share) == pytest.approx((1 + 2 + 3) / 3)


def test_bootstrap_ci_contains_mean():
    vals = np.arange(100, dtype=float)
    mean, lo, hi = M.bootstrap_ci(vals)
    assert mean == pytest.approx(49.5) and lo < mean < hi