"""Ratings preparation and splits (spec 4.4), as pure functions over DataFrames.

Columns used: user_id, ml_movie_id, rating, timestamp.
"""
import numpy as np
import pandas as pd

TRAIN_PCT, VAL_PCT = 70, 10   # test gets the remaining newest 20%


def scale_to_10(stars: pd.Series) -> pd.Series:
    """MovieLens 0.5-5.0 stars x 2 = CineMatch 1-10."""
    return (stars.astype("float32") * 2).round().astype("int8")


def filter_and_sample(ratings: pd.DataFrame, film_ids, min_ratings: int, n_users: int, seed: int) -> pd.DataFrame:
    """Keep ratings on catalog films, users with >= min_ratings of them, then sample users."""
    r = ratings[ratings["ml_movie_id"].isin(film_ids)]
    counts = r.groupby("user_id").size()
    eligible = np.sort(counts[counts >= min_ratings].index.to_numpy())
    rng = np.random.default_rng(seed)
    chosen = rng.choice(eligible, size=min(n_users, len(eligible)), replace=False)
    return r[r["user_id"].isin(chosen)].reset_index(drop=True)


def time_split(ratings: pd.DataFrame) -> pd.Series:
    """Per user, by time: oldest 70% 'train', next 10% 'val', newest 20% 'test'.

    Ties on timestamp are broken by film id so the split is deterministic.
    """
    r = ratings.sort_values(["user_id", "timestamp", "ml_movie_id"])
    pos = r.groupby("user_id").cumcount()
    n = r.groupby("user_id")["user_id"].transform("size")
    # Integer percentages: float fractions (0.7 + 0.1 = 0.7999...) shift the boundaries.
    n_train = n * TRAIN_PCT // 100
    n_val_end = n * (TRAIN_PCT + VAL_PCT) // 100
    split = np.where(pos < n_train, "train", np.where(pos < n_val_end, "val", "test"))
    return pd.Series(split, index=r.index).reindex(ratings.index)


def global_cutoff(timestamps: pd.Series, test_frac: float = 0.20) -> int:
    """The timestamp after which about `test_frac` of all ratings fall."""
    return int(np.quantile(timestamps.to_numpy(), 1 - test_frac))


def holdout_films(film_ids, frac: float, seed: int) -> np.ndarray:
    """Pick `frac` of the films (sorted ids, fixed seed) for the new-movie test."""
    ids = np.sort(np.asarray(list(film_ids)))
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(ids, size=int(round(len(ids) * frac)), replace=False))