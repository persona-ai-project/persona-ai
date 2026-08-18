"""add digital twin tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Twin Categories
    op.create_table(
        "twin_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Twins
    op.create_table(
        "twins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("twin_categories.id"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("tagline", sa.Text(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("is_public_figure", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("public_figure_name", sa.Text(), nullable=True),
        sa.Column("verification_level", sa.Text(), nullable=False, server_default="unverified"),
        sa.Column("personality_config", postgresql.JSONB(), nullable=True),
        sa.Column("boundaries", postgresql.JSONB(), nullable=True),
        sa.Column("knowledge_anchors", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("visibility", sa.Text(), nullable=False, server_default="private"),
        sa.Column("total_chats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_messages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_fidelity", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_twins_owner_id", "twins", ["owner_id"])
    op.create_index("ix_twins_category_id", "twins", ["category_id"])
    op.create_index("ix_twins_slug", "twins", ["slug"])
    op.create_index("ix_twins_status", "twins", ["status"])
    op.create_index("ix_twins_visibility", "twins", ["visibility"])

    # Sources
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("twin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("twins.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("file_key", sa.Text(), nullable=True),
        sa.Column("file_name", sa.Text(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sources_twin_id", "sources", ["twin_id"])
    op.create_index("ix_sources_user_id", "sources", ["user_id"])
    op.create_index("ix_sources_status", "sources", ["status"])

    # Knowledge Items
    op.create_table(
        "knowledge_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("twin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("twins.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("embedding_id", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_knowledge_items_twin_id", "knowledge_items", ["twin_id"])
    op.create_index("ix_knowledge_items_source_id", "knowledge_items", ["source_id"])
    op.create_index("ix_knowledge_items_content_type", "knowledge_items", ["content_type"])

    # Interview Sessions
    op.create_table(
        "interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("twin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("twins.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.Column("questions_asked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("messages_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_extracted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_interview_sessions_twin_id", "interview_sessions", ["twin_id"])
    op.create_index("ix_interview_sessions_user_id", "interview_sessions", ["user_id"])
    op.create_index("ix_interview_sessions_status", "interview_sessions", ["status"])

    # Interview Messages
    op.create_table(
        "interview_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("knowledge_items_extracted", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_interview_messages_session_id", "interview_messages", ["session_id"])

    # Subscription Plans
    op.create_table(
        "subscription_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("max_twins", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_sources_per_twin", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_messages_per_day", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("max_interview_sessions", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("features", postgresql.JSONB(), nullable=True),
        sa.Column("price_monthly", sa.Integer(), nullable=True),
        sa.Column("price_yearly", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # User Subscriptions
    op.create_table(
        "user_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("current_period_start", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("twins_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("messages_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("messages_reset_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_subscriptions_user_id", "user_subscriptions", ["user_id"])
    op.create_index("ix_user_subscriptions_status", "user_subscriptions", ["status"])
    op.create_unique_constraint("uq_user_subscriptions_user_id", "user_subscriptions", ["user_id"])

    # Twin Access Logs
    op.create_table(
        "twin_access_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("twin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("twins.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_twin_access_logs_twin_id", "twin_access_logs", ["twin_id"])
    op.create_index("ix_twin_access_logs_created_at", "twin_access_logs", ["created_at"])

    # Seed default subscription plans
    op.execute("""
        INSERT INTO subscription_plans (id, name, display_name, description, max_twins, max_sources_per_twin, max_messages_per_day, max_interview_sessions, features, price_monthly, price_yearly)
        VALUES
            ('a0000000-0000-0000-0000-000000000001', 'free', 'Free', 'Get started with 1 twin', 1, 5, 100, 3, '["basic_chat", "interview", "5_sources"]', NULL, NULL),
            ('a0000000-0000-0000-0000-000000000002', 'pro', 'Pro', 'For power users and creators', 5, 25, 500, 10, '["unlimited_chat", "interview", "25_sources", "analytics", "priority_support"]', 1999, 19999),
            ('a0000000-0000-0000-0000-000000000003', 'enterprise', 'Enterprise', 'For organizations and public figures', 25, 100, 10000, 50, '["everything_in_pro", "100_sources", "api_access", "custom_branding", "dedicated_support", "sla"]', 9999, 99999)
    """)

    # Assign free plan to all existing users
    op.execute("""
        INSERT INTO user_subscriptions (id, user_id, plan_id, status, current_period_start, current_period_end)
        SELECT
            gen_random_uuid(),
            u.id,
            'a0000000-0000-0000-0000-000000000001',
            'active',
            NOW(),
            NOW() + INTERVAL '1 year'
        FROM users u
        WHERE NOT EXISTS (
            SELECT 1 FROM user_subscriptions us WHERE us.user_id = u.id
        )
    """)


def downgrade() -> None:
    op.drop_table("twin_access_logs")
    op.drop_table("user_subscriptions")
    op.drop_table("subscription_plans")
    op.drop_table("interview_messages")
    op.drop_table("interview_sessions")
    op.drop_table("knowledge_items")
    op.drop_table("sources")
    op.drop_table("twins")
    op.drop_table("twin_categories")
