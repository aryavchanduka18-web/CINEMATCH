"""Export live site feedback for the next retrain (spec section 4.5, "any" step; run by hand).

Writes data/processed/site_feedback/ratings.parquet (explicit: site ratings on MovieLens films, in the
same user_id / ml_movie_id / rating / timestamp layout as the MovieLens splits) and events.parquet
(implicit: every interaction with its event weight). Site users get ids from 100,000,000 upward so
they can never collide with MovieLens user ids. To retrain with them, append ratings.parquet to
splits/train.parquet and rerun steps 9-11.
"""
import pandas as pd
from sqlalchemy import create_engine, text

from cinematch_engine.config import event_weights
from pipeline.common import PROCESSED, env, get_logger

log = get_logger("export_site_feedback")
SITE_USER_OFFSET = 100_000_000


def main() -> None:
    out = PROCESSED / "site_feedback"
    out.mkdir(parents=True, exist_ok=True)
    engine = create_engine(env("DATABASE_URL"))
    with engine.connect() as conn:
        ratings = pd.DataFrame(conn.execute(text("""
            SELECT r.user_id + :off AS user_id, m.ml_movie_id, r.rating::smallint AS rating,
                   extract(epoch FROM r.updated_at)::bigint AS timestamp
            FROM ratings r JOIN movies m ON m.id = r.movie_id
            WHERE m.ml_movie_id IS NOT NULL"""), {"off": SITE_USER_OFFSET}).mappings().all())
        events = pd.DataFrame(conn.execute(text("""
            SELECT i.user_id + :off AS user_id, m.ml_movie_id, m.tmdb_id, i.event_type, i.value, i.source, i.created_at
            FROM interactions i JOIN movies m ON m.id = i.movie_id"""), {"off": SITE_USER_OFFSET}).mappings().all())
    weights = event_weights()
    if len(events):
        events["weight"] = events["event_type"].map(weights).fillna(0.0)
    ratings.to_parquet(out / "ratings.parquet", index=False)
    events.to_parquet(out / "events.parquet", index=False)
    log.info("exported %d site ratings on MovieLens films and %d events", len(ratings), len(events))


if __name__ == "__main__":
    main()