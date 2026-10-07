"""initial schema: catalogue, users, current-state tables, logs

Revision ID: 0001
Revises:
Create Date: 2026-10-08
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

from app.models.catalog import SEARCH_VECTOR_SQL

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _now() -> sa.TextClause:
    return sa.text("now()")


def _user_fk() -> sa.Column:
    return sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


def _movie_fk() -> sa.Column:
    return sa.Column("movie_id", sa.Integer, sa.ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    # ---- catalogue -------------------------------------------------------
    op.create_table(
        "movies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tmdb_id", sa.Integer, nullable=False, unique=True),
        sa.Column("ml_movie_id", sa.Integer, unique=True),
        sa.Column("imdb_id", sa.Text),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("original_title", sa.Text),
        sa.Column("overview", sa.Text),
        sa.Column("release_date", sa.Date),
        sa.Column("year", sa.SmallInteger),
        sa.Column("runtime_min", sa.SmallInteger),
        sa.Column("original_language", sa.String(3)),
        sa.Column("spoken_languages", pg.ARRAY(sa.Text)),
        sa.Column("countries", pg.ARRAY(sa.Text)),
        sa.Column("certification", sa.Text),
        sa.Column("poster_path", sa.Text),
        sa.Column("backdrop_path", sa.Text),
        sa.Column("dominant_color", sa.CHAR(7)),
        sa.Column("tagline", sa.Text),
        sa.Column("studios", pg.ARRAY(sa.Text)),
        sa.Column("logo_path", sa.Text),
        sa.Column("catalog_part", sa.CHAR(1)),
        sa.Column("ml_rating_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ml_rating_mean", sa.Numeric(4, 2)),
        sa.Column("rating_hist", pg.ARRAY(sa.Integer)),
        sa.Column("popularity_score", sa.REAL),
        sa.Column("tmdb_vote_count", sa.Integer),
        sa.Column("search_vector", pg.TSVECTOR, sa.Computed(SEARCH_VECTOR_SQL, persisted=True)),
        sa.CheckConstraint("catalog_part IN ('A','B','C')", name="ck_movies_catalog_part"),
    )
    op.create_index("ix_movies_search_vector", "movies", ["search_vector"], postgresql_using="gin")

    op.create_table(
        "genres",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("slug", sa.Text, nullable=False, unique=True),
    )
    op.create_table(
        "movie_genres",
        _movie_fk(),
        sa.Column("genre_id", sa.Integer, sa.ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_movie_genres_genre_id", "movie_genres", ["genre_id"])

    op.create_table(
        "people",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tmdb_person_id", sa.Integer, unique=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("profile_path", sa.Text),
    )
    op.create_table(
        "movie_credits",
        _movie_fk(),
        sa.Column("person_id", sa.Integer, sa.ForeignKey("people.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.Text, primary_key=True),
        sa.Column("character", sa.Text),
        sa.Column("credit_order", sa.SmallInteger),
        sa.CheckConstraint("role IN ('cast','director','writer')", name="ck_movie_credits_role"),
    )
    op.create_index("ix_movie_credits_person_id", "movie_credits", ["person_id"])

    op.create_table(
        "keywords",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, unique=True),
    )
    op.create_table(
        "movie_keywords",
        _movie_fk(),
        sa.Column("keyword_id", sa.Integer, sa.ForeignKey("keywords.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_movie_keywords_keyword_id", "movie_keywords", ["keyword_id"])

    op.create_table(
        "movie_awards",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("movie_id", sa.Integer, sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("award", sa.Text, nullable=False),
        sa.Column("category", sa.Text),
        sa.Column("year", sa.SmallInteger),
        sa.Column("result", sa.Text, nullable=False),
        sa.Column("wikidata_id", sa.Text),
        sa.CheckConstraint("result IN ('won','nominated')", name="ck_movie_awards_result"),
    )
    op.create_index("ix_movie_awards_movie_id", "movie_awards", ["movie_id"])

    # ---- users and current state ----------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", pg.CITEXT, unique=True),
        sa.Column("password_hash", sa.Text),
        sa.Column("display_name", sa.Text),
        sa.Column("is_guest", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.Column("onboarded_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "user_preferences",
        _user_fk(),
        sa.Column("languages", pg.ARRAY(sa.Text)),
        sa.Column("liked_genre_ids", pg.ARRAY(sa.Integer)),
        sa.Column("disliked_genre_ids", pg.ARRAY(sa.Integer)),
        sa.Column("discovery_mode", sa.Text, nullable=False, server_default="balanced"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_now()),
        sa.CheckConstraint(
            "discovery_mode IN ('familiar','balanced','discover')",
            name="ck_user_preferences_discovery_mode",
        ),
    )
    op.create_table(
        "onboarding_picks",
        _user_fk(),
        _movie_fk(),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
    )
    op.create_table(
        "ratings",
        _user_fk(),
        _movie_fk(),
        sa.Column("rating", sa.SmallInteger, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.CheckConstraint("rating BETWEEN 1 AND 10", name="ck_ratings_rating"),
    )
    op.create_table(
        "reactions",
        _user_fk(),
        _movie_fk(),
        sa.Column("value", sa.SmallInteger, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.CheckConstraint("value IN (-1, 1)", name="ck_reactions_value"),
    )
    op.create_table(
        "user_movie_list",
        _user_fk(),
        _movie_fk(),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
    )
    op.create_table(
        "watched",
        _user_fk(),
        _movie_fk(),
        sa.Column("marked_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
    )
    # The user_id side is covered by each composite primary key; index the movie side.
    for table in ("onboarding_picks", "ratings", "reactions", "user_movie_list", "watched"):
        op.create_index(f"ix_{table}_movie_id", table, ["movie_id"])

    # ---- append-only logs -----------------------------------------------
    op.create_table(
        "interactions",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movie_id", sa.Integer, sa.ForeignKey("movies.id", ondelete="CASCADE")),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column("value", sa.REAL),
        sa.Column("source", sa.Text),
        sa.Column("position", sa.SmallInteger),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
    )
    op.create_index(
        "ix_interactions_user_id_created_at", "interactions", ["user_id", sa.text("created_at DESC")]
    )
    op.create_index("ix_interactions_movie_id", "interactions", ["movie_id"])

    op.create_table(
        "recommendation_logs",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("request_id", pg.UUID(as_uuid=True)),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("surface", sa.Text),
        sa.Column("movie_id", sa.Integer, sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rank", sa.SmallInteger),
        sa.Column("final_score", sa.REAL),
        sa.Column("match_pct", sa.SmallInteger),
        sa.Column("components", pg.JSONB),
        sa.Column("reason_code", sa.Text),
        sa.Column("mode", sa.Text),
        sa.Column("page_id", pg.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
    )
    op.create_index("ix_recommendation_logs_request_id", "recommendation_logs", ["request_id"])
    op.create_index("ix_recommendation_logs_user_id", "recommendation_logs", ["user_id"])
    op.create_index("ix_recommendation_logs_movie_id", "recommendation_logs", ["movie_id"])


def downgrade() -> None:
    for table in (
        "recommendation_logs", "interactions", "watched", "user_movie_list", "reactions",
        "ratings", "onboarding_picks", "user_preferences", "users", "movie_awards",
        "movie_keywords", "keywords", "movie_credits", "people", "movie_genres", "genres", "movies",
    ):
        op.drop_table(table)