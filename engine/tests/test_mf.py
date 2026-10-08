"""Matrix factorization models and their fold-in, on small synthetic data."""
import numpy as np
import pytest
import scipy.sparse as sp

from cinematch_engine.models.als_implicit import ImplicitALS, implicit_strength
from cinematch_engine.models.svd import FunkSVD


def _ratings(seed=0, n_users=60, n_items=40, density=0.3):
    rng = np.random.default_rng(seed)
    taste = rng.normal(size=(n_users, 3))
    kind = rng.normal(size=(n_items, 3))
    full = np.clip(np.round(5.5 + 1.5 * taste @ kind.T / np.sqrt(3)), 1, 10)
    mask = rng.random((n_users, n_items)) < density
    return sp.csr_matrix(np.where(mask, full, 0).astype(np.float32))


def test_implicit_strength_keeps_only_ratings_from_7():
    w = implicit_strength(sp.csr_matrix(np.array([[10, 7, 6, 2]], dtype=np.float32)))
    assert w.toarray().tolist() == [[4, 1, 0, 0]]


def test_als_fold_in_matches_library_recalculation():
    train = implicit_strength(_ratings())
    m = ImplicitALS(factors=4, regularization=0.1, alpha=5.0, iterations=10).fit(train)
    u = int(np.argmax(np.diff(train.indptr)))
    row = train[u]
    mine = m.fold_in(row.indices, row.data)
    conf = row.copy()
    conf.data = 1.0 + m.alpha * conf.data
    theirs = np.asarray(m.model.recalculate_user(u, conf)).ravel()
    # The library solves the same system iteratively (conjugate gradient), so allow a small gap.
    assert np.corrcoef(mine, theirs)[0, 1] > 0.99


def test_svd_fold_in_fits_the_users_ratings():
    train = _ratings(1)
    m = FunkSVD(n_factors=3, n_epochs=40, lr_all=0.01, reg_all=0.05).fit(train)
    u = int(np.argmax(np.diff(train.indptr)))
    row = train[u]
    p, bu = m.fold_in(row.indices, row.data, reg=1.0)
    err_fold = np.mean((m.score_vector(p, bu)[row.indices] - row.data) ** 2)
    err_zero = np.mean((m.score_vector(np.zeros_like(p), 0.0)[row.indices] - row.data) ** 2)
    assert err_fold < err_zero
    assert m.predict(np.array([u]), np.array([row.indices[0]]))[0] == pytest.approx(
        np.clip(m.score(np.array([u]))[0, row.indices[0]], 1, 10), abs=1e-4)