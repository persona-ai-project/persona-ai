"""add twin_id to messages

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-21
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add twin_id column to messages table
    op.add_column(
        "messages",
        sa.Column("twin_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    # Add FK constraint
    op.create_foreign_key(
        "fk_messages_twin_id",
        "messages",
        "twins",
        ["twin_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Add index for fast lookups
    op.create_index("ix_messages_twin_id", "messages", ["twin_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_twin_id", table_name="messages")
    op.drop_constraint("fk_messages_twin_id", "messages", type_="foreignkey")
    op.drop_column("messages", "twin_id")
