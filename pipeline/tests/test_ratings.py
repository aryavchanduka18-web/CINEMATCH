import numpy as np
import pandas as pd

from pipeline.ratings import filter_and_sample, global_cutoff, holdout_films, scale_to_10, time_split


def test_scale_to_10_maps_every_half_star():
    stars = pd.Series([0.5, 1.0, 2.5, 3.5, 4.5, 5.0])
    assert scale_to_10(stars).tolist() == [1, 2, 5, 7, 9, 10]


def _ratings(n_users=3, per_user=20):
    rows = []
    rng = np.random.default_rng(0)
    for u in range(1, n_users + 1):
        ts = rng.permutation(per_user) * 100 + u
        for i, t in enumerate(ts):
            rows.append({"user_id": u, "ml_movie_id": i, "rating": 8, "timestamp": int(t)})
    return pd.DataFrame(rows)


def test_time_split_sizes_and_order():
    r = _ratings(per_user=20)
    r["split"] = time_split(r)
    for _, g in r.groupby("user_id"):
        counts = g["split"].value_counts()
        assert (counts["train"], counts["val"], counts["test"]) == (14, 2, 4)
        # Every train rating is older than every val rating, which is older than every test rating.
        assert g.loc[g.split == "train", "timestamp"].max() < g.loc[g.split == "val", "timestamp"].min()
        assert g.loc[g.split == "val", "timestamp"].max() < g.loc[g.split == "test", "timestamp"].min()


def test_filter_and_sample_keeps_catalog_films_and_active_users():
    r = pd.concat([_ratings(n_users=5, per_user=25), pd.DataFrame(
        [{"user_id": 99, "ml_movie_id": i, "rating": 8, "timestamp": i} for i in range(10)])])
    out = filter_and_sample(r, film_ids=set(range(22)), min_ratings=20, n_users=3, seed=42)
    assert out["ml_movie_id"].max() < 22
    assert out["user_id"].nunique() == 3 and 99 not in set(out["user_id"])
    again = filter_and_sample(r, film_ids=set(range(22)), min_ratings=20, n_users=3, seed=42)
    assert set(out["user_id"]) == set(again["user_id"])          # fixed seed is reproducible


def test_global_cutoff_puts_about_20_percent_after():
    ts = pd.Series(range(1000))
    cut = global_cutoff(ts)
    assert abs((ts > cut).mean() - 0.20) < 0.01


def test_holdout_is_5_percent_and_reproducible():
    films = range(1000)
    a, b = holdout_films(films, 0.05, 42), holdout_films(films, 0.05, 42)
    assert len(a) == 50 and (a == b).all() and len(set(a)) == 50