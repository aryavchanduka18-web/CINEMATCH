"""Step 6: ratings on the evaluation backbone (part A, original gate), users with >= 20 of them, 30,000 sampled users, x2 scale."""
import pandas as pd

from pipeline.catalog import backbone_ml_ids
from pipeline.common import ML_DIR, PROCESSED, SEED, get_logger, write_json
from pipeline.ratings import filter_and_sample, scale_to_10

log = get_logger("06_ratings")
MIN_RATINGS, N_USERS = 20, 30_000


def main() -> None:
    catalog = pd.read_csv(PROCESSED / "catalog_ids.csv")
    film_ids = backbone_ml_ids(catalog)
    raw = pd.read_csv(
        ML_DIR / "ratings.csv", engine="pyarrow",
        dtype={"userId": "int32", "movieId": "int32", "rating": "float32", "timestamp": "int64"},
    ).rename(columns={"userId": "user_id", "movieId": "ml_movie_id"})
    sample = filter_and_sample(raw, set(film_ids), MIN_RATINGS, N_USERS, SEED)
    sample["rating"] = scale_to_10(sample["rating"])
    sample.to_parquet(PROCESSED / "ratings.parquet", index=False)
    summary = {
        "users": int(sample["user_id"].nunique()), "ratings": int(len(sample)),
        "films": int(sample["ml_movie_id"].nunique()), "min_ratings_per_user": MIN_RATINGS, "seed": SEED,
        "rating_distribution": sample["rating"].value_counts().sort_index().to_dict(),
    }
    write_json(PROCESSED / "ratings_summary.json", summary)
    log.info("%s", {k: summary[k] for k in ("users", "ratings", "films")})


if __name__ == "__main__":
    main()