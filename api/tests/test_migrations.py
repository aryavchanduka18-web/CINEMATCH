from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

from app.models import Base

EXPECTED_TABLES = {
    "movies", "genres", "movie_genres", "people", "movie_credits", "keywords",
    "movie_keywords", "movie_awards", "users", "user_preferences", "onboarding_picks",
    "ratings", "reactions", "user_movie_list", "watched", "interactions", "recommendation_logs",
}


def test_migration_creates_all_tables(test_engine):
    tables = set(inspect(test_engine).get_table_names())
    assert EXPECTED_TABLES <= tables


def test_citext_extension_enabled(test_engine):
    with test_engine.connect() as conn:
        assert conn.execute(text("select 1 from pg_extension where extname = 'citext'")).scalar() == 1


def test_migration_matches_models(test_engine):
    """The hand-written migration and the SQLAlchemy models must describe the same schema."""
    with test_engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []


def test_deleting_user_cascades_to_owned_rows(test_engine):
    with test_engine.begin() as conn:
        movie_id = conn.execute(text("insert into movies (tmdb_id, title) values (-2, 'X') returning id")).scalar()
        user_id = conn.execute(text("insert into users (display_name) values ('t') returning id")).scalar()
        conn.execute(text("insert into ratings (user_id, movie_id, rating) values (:u, :m, 8)"), {"u": user_id, "m": movie_id})
        conn.execute(text("insert into interactions (user_id, movie_id, event_type) values (:u, :m, 'like')"), {"u": user_id, "m": movie_id})
        conn.execute(text("delete from users where id = :u"), {"u": user_id})
        left = conn.execute(
            text("select (select count(*) from ratings where user_id = :u) + (select count(*) from interactions where user_id = :u)"),
            {"u": user_id},
        ).scalar()
        conn.execute(text("delete from movies where id = :m"), {"m": movie_id})
    assert left == 0