"""franchises: movies.collection_id and collection_name (TMDB collections)

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("movies", sa.Column("collection_id", sa.Integer))
    op.add_column("movies", sa.Column("collection_name", sa.Text))
    op.create_index("ix_movies_collection_id", "movies", ["collection_id"])


def downgrade() -> None:
    op.drop_index("ix_movies_collection_id", table_name="movies")
    op.drop_column("movies", "collection_name")
    op.drop_column("movies", "collection_id")
