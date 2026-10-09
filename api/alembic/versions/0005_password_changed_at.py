"""accounts: users.password_changed_at (sessions issued earlier stop working)

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-08
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("users", "password_changed_at")
