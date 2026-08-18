"""add voice configuration to twins

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add voice configuration to twins
    op.add_column("twins", sa.Column("voice_id", sa.Text(), server_default="en_US-lessac-medium"))
    op.add_column("twins", sa.Column("voice_enabled", sa.Boolean(), server_default="true"))
    op.add_column("twins", sa.Column("voice_speed", sa.Float(), server_default="1.0"))
    op.add_column("twins", sa.Column("voice_pitch", sa.Float(), server_default="1.0"))
    
    # Update existing twins
    op.execute("""
        UPDATE twins 
        SET voice_id = 'en_US-lessac-medium', voice_enabled = true, voice_speed = 1.0, voice_pitch = 1.0
        WHERE voice_id IS NULL
    """)


def downgrade() -> None:
    op.drop_column("twins", "voice_pitch")
    op.drop_column("twins", "voice_speed")
    op.drop_column("twins", "voice_enabled")
    op.drop_column("twins", "voice_id")
