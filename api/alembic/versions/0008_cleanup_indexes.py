"""Indexes for the housekeeping job: old recommendation logs and idle guests.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_recommendation_logs_created_at", "recommendation_logs", ["created_at"])
    op.execute("CREATE INDEX ix_users_guest_created_at ON users (created_at) WHERE is_guest")


def downgrade() -> None:
    op.drop_index("ix_users_guest_created_at", table_name="users")
    op.drop_index("ix_recommendation_logs_created_at", table_name="recommendation_logs")
