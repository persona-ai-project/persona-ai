"""initial schema - all 9 tables

Revision ID: 0001
Revises:
Create Date: 2026-05-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # 1. users
    op.create_table("users",
        sa.Column("id",         UUID(as_uuid=True), primary_key=True),
        sa.Column("email",      sa.Text(), nullable=False, unique=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("is_active",  sa.Boolean(), nullable=False, default=True),
    )

    # 2. personas
    op.create_table("personas",
        sa.Column("id",           UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",      UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name",         sa.Text(), nullable=False),
        sa.Column("persona_blob", JSONB(), nullable=True),
        sa.Column("created_at",   sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("is_active",    sa.Boolean(), nullable=False, default=True),
    )
    op.create_index("ix_personas_user_id", "personas", ["user_id"])

    # 3. persona_versions
    op.create_table("persona_versions",
        sa.Column("id",             UUID(as_uuid=True), primary_key=True),
        sa.Column("persona_id",     UUID(as_uuid=True), sa.ForeignKey("personas.id"), nullable=False),
        sa.Column("user_id",        UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("persona_blob",   JSONB(), nullable=True),
        sa.Column("created_at",     sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_persona_versions_user_id",   "persona_versions", ["user_id"])
    op.create_index("ix_persona_versions_persona_id","persona_versions", ["persona_id"])

    # 4. messages
    op.create_table("messages",
        sa.Column("id",         UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",    UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("persona_id", UUID(as_uuid=True), sa.ForeignKey("personas.id"), nullable=True),
        sa.Column("role",       sa.Text(), nullable=False),
        sa.Column("content",    sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_messages_user_id",    "messages", ["user_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])

    # 5. feedback
    op.create_table("feedback",
        sa.Column("id",         UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",    UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("message_id", UUID(as_uuid=True), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("rating",     sa.Integer(), nullable=True),
        sa.Column("comment",    sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_feedback_user_id",    "feedback", ["user_id"])
    op.create_index("ix_feedback_created_at", "feedback", ["created_at"])

    # 6. preference_pairs
    op.create_table("preference_pairs",
        sa.Column("id",         UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",    UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("prompt",     sa.Text(), nullable=False),
        sa.Column("chosen",     sa.Text(), nullable=False),
        sa.Column("rejected",   sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_preference_pairs_user_id", "preference_pairs", ["user_id"])

    # 7. daily_questions_asked
    op.create_table("daily_questions_asked",
        sa.Column("id",        UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",   UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("question",  sa.Text(), nullable=False),
        sa.Column("asked_at",  sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_daily_questions_user_id", "daily_questions_asked", ["user_id"])

    # 8. ingestion_jobs
    op.create_table("ingestion_jobs",
        sa.Column("id",         UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",    UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status",     sa.Text(), nullable=False, server_default="pending"),
        sa.Column("source",     sa.Text(), nullable=True),
        sa.Column("error",      sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_ingestion_jobs_user_id", "ingestion_jobs", ["user_id"])

    # 9. voice_cache
    op.create_table("voice_cache",
        sa.Column("id",         UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id",    UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("text_hash",  sa.Text(), nullable=False),
        sa.Column("audio_url",  sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_voice_cache_user_id",   "voice_cache", ["user_id"])
    op.create_index("ix_voice_cache_text_hash", "voice_cache", ["text_hash"])


def downgrade() -> None:
    op.drop_table("voice_cache")
    op.drop_table("ingestion_jobs")
    op.drop_table("daily_questions_asked")
    op.drop_table("preference_pairs")
    op.drop_table("feedback")
    op.drop_table("messages")
    op.drop_table("persona_versions")
    op.drop_table("personas")
    op.drop_table("users")