"""Step 12: load movies, genres, people, keywords, awards, aggregates and colors into Postgres."""
import pandas as pd
from sqlalchemy import create_engine

from pipeline.common import PROCESSED, env, get_logger, write_json
from pipeline.loader import load_catalog

log = get_logger("12_load_db")


def main() -> None:
    movies = pd.read_parquet(PROCESSED / "movies_clean.parquet")
    credits = pd.read_parquet(PROCESSED / "credits_clean.parquet")
    awards = pd.read_parquet(PROCESSED / "awards.parquet")
    aggregates = pd.read_parquet(PROCESSED / "ml_aggregates.parquet")
    if len(movies) < 1000:  # a broken earlier step must never prune the whole catalog
        raise RuntimeError(f"movies_clean.parquet has only {len(movies)} films; refusing to load")
    engine = create_engine(env("DATABASE_URL"))
    counts = load_catalog(engine, movies, credits, awards, aggregates)
    engine.dispose()
    write_json(PROCESSED / "db_counts.json", counts)
    log.info("row counts: %s", counts)


if __name__ == "__main__":
    main()