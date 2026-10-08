"""typo-tolerant search: pg_trgm + normalized title with a trigram index

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-08
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.models.catalog import TITLE_NORM_SQL

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.add_column("movies", sa.Column("title_norm", sa.Text, sa.Computed(TITLE_NORM_SQL, persisted=True)))
    op.create_index("ix_movies_title_norm_trgm", "movies", ["title_norm"], postgresql_using="gin",
                    postgresql_ops={"title_norm": "gin_trgm_ops"})


def downgrade() -> None:
    op.drop_index("ix_movies_title_norm_trgm", table_name="movies")
    op.drop_column("movies", "title_norm")
