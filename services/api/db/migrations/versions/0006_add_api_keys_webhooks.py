"""add api keys and webhooks

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # API Keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("key_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("key_prefix", sa.Text(), nullable=False),  # first 8 chars for display
        sa.Column("scopes", postgresql.JSONB(), server_default="[]"),  # list of allowed endpoints
        sa.Column("rate_limit", sa.Integer(), server_default="1000"),  # requests per day
        sa.Column("daily_usage", sa.Integer(), server_default="0"),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"])
    
    # API Usage Log table
    op.create_table(
        "api_usage_logs",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("api_key_id", sa.Text(), sa.ForeignKey("api_keys.id"), nullable=False),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("method", sa.Text(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("request_size", sa.Integer(), nullable=True),
        sa.Column("response_size", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_api_usage_logs_api_key_id", "api_usage_logs", ["api_key_id"])
    op.create_index("ix_api_usage_logs_user_id", "api_usage_logs", ["user_id"])
    op.create_index("ix_api_usage_logs_created_at", "api_usage_logs", ["created_at"])
    
    # Webhooks table
    op.create_table(
        "webhooks",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("events", postgresql.JSONB(), nullable=False),  # list of event types
        sa.Column("secret", sa.Text(), nullable=False),  # for signature verification
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("last_triggered_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_webhooks_user_id", "webhooks", ["user_id"])
    
    # Webhook Deliveries table
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("webhook_id", sa.Text(), sa.ForeignKey("webhooks.id"), nullable=False),
        sa.Column("event", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),  # pending, success, failed
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0"),
        sa.Column("next_retry_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_webhook_deliveries_webhook_id", "webhook_deliveries", ["webhook_id"])
    op.create_index("ix_webhook_deliveries_status", "webhook_deliveries", ["status"])
    


def downgrade() -> None:
    op.drop_table("webhook_deliveries")
    op.drop_table("webhooks")
    op.drop_table("api_usage_logs")
    op.drop_table("api_keys")
