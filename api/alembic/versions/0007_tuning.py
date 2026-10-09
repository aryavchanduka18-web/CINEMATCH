"""v2: user_preferences.tuning (the Tune sliders)

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_preferences", sa.Column("tuning", JSONB))


def downgrade() -> None:
    op.drop_column("user_preferences", "tuning")
