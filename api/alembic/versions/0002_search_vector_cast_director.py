"""search_vector: title + cast + director (spec section 10), filled by the catalog loader

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-08
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_movies_search_vector", table_name="movies")
    op.drop_column("movies", "search_vector")
    op.add_column("movies", sa.Column("search_vector", pg.TSVECTOR))
    op.create_index("ix_movies_search_vector", "movies", ["search_vector"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_index("ix_movies_search_vector", table_name="movies")
    op.drop_column("movies", "search_vector")
    op.add_column("movies", sa.Column("search_vector", pg.TSVECTOR, sa.Computed(
        "setweight(to_tsvector('simple'::regconfig, coalesce(title, '')), 'A') || "
        "setweight(to_tsvector('simple'::regconfig, coalesce(original_title, '')), 'A') || "
        "setweight(to_tsvector('simple'::regconfig, coalesce(tagline, '')), 'B') || "
        "setweight(to_tsvector('simple'::regconfig, coalesce(overview, '')), 'C')",
        persisted=True)))
    op.create_index("ix_movies_search_vector", "movies", ["search_vector"], postgresql_using="gin")