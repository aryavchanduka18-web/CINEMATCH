"""catalog part D (Hollywood enrichment)

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-08
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_movies_catalog_part", "movies", type_="check")
    op.create_check_constraint("ck_movies_catalog_part", "movies", "catalog_part IN ('A','B','C','D')")


def downgrade() -> None:
    op.execute("DELETE FROM movies WHERE catalog_part = 'D'")
    op.drop_constraint("ck_movies_catalog_part", "movies", type_="check")
    op.create_check_constraint("ck_movies_catalog_part", "movies", "catalog_part IN ('A','B','C')")