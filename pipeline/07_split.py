"""Step 7: per-user time split (70/10/20), global time-cutoff split, and the new-movie holdout.

The holdout films (5% of part A) lose all their ratings from train/val/test; their ratings
go to newmovie_test.parquet and are used only in the new-movie experiment.
"""
from datetime import datetime, timezone

import pandas as pd

from pipeline.catalog import backbone_ml_ids
from pipeline.common import PROCESSED, SEED, get_logger, write_json
from pipeline.ratings import global_cutoff, holdout_films, time_split

log = get_logger("07_split")
OUT = PROCESSED / "splits"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ratings = pd.read_parquet(PROCESSED / "ratings.parquet")
    catalog = pd.read_csv(PROCESSED / "catalog_ids.csv")
    part_a = backbone_ml_ids(catalog)

    held = holdout_films(part_a, 0.05, SEED)
    pd.DataFrame({"ml_movie_id": held}).to_parquet(OUT / "holdout_films.parquet", index=False)
    is_held = ratings["ml_movie_id"].isin(held)
    ratings[is_held].to_parquet(OUT / "newmovie_test.parquet", index=False)
    main_r = ratings[~is_held].reset_index(drop=True)

    main_r["split"] = time_split(main_r)
    sizes = {}
    for name in ("train", "val", "test"):
        part = main_r[main_r["split"] == name].drop(columns="split")
        part.to_parquet(OUT / f"{name}.parquet", index=False)
        sizes[name] = int(len(part))

    cutoff = global_cutoff(main_r["timestamp"])
    after = main_r["timestamp"] > cutoff
    main_r[~after].drop(columns="split").to_parquet(OUT / "global_train.parquet", index=False)
    main_r[after].drop(columns="split").to_parquet(OUT / "global_test.parquet", index=False)

    summary = {
        "per_user_split": sizes,
        "global_cutoff_timestamp": cutoff,
        "global_cutoff_date": datetime.fromtimestamp(cutoff, tz=timezone.utc).date().isoformat(),
        "global_split": {"train": int((~after).sum()), "test": int(after.sum())},
        "holdout_films": int(len(held)),
        "holdout_films_with_ratings_in_sample": int(ratings.loc[is_held, "ml_movie_id"].nunique()),
        "newmovie_test_ratings": int(is_held.sum()),
        "seed": SEED,
    }
    write_json(PROCESSED / "split_summary.json", summary)
    log.info("%s", summary)


if __name__ == "__main__":
    main()