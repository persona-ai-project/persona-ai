"""add language support to twins

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add language support to twins
    op.add_column("twins", sa.Column("languages", postgresql.JSONB(), server_default='["en"]'))
    op.add_column("twins", sa.Column("default_language", sa.Text(), server_default="en"))
    op.add_column("twins", sa.Column("auto_detect_language", sa.Boolean(), server_default="true"))
    
    # Update existing twins to have English as default
    op.execute("""
        UPDATE twins 
        SET languages = '["en"]', default_language = 'en', auto_detect_language = true
        WHERE languages IS NULL
    """)


def downgrade() -> None:
    op.drop_column("twins", "auto_detect_language")
    op.drop_column("twins", "default_language")
    op.drop_column("twins", "languages")
