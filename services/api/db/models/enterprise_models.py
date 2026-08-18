"""
db/models/enterprise_models.py
==============================
Enterprise feature models: API keys, webhooks, API usage logs.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Text, Boolean, Integer, Float, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship
from db.base import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id          = Column(Text, primary_key=True)
    user_id     = Column(Text, ForeignKey("users.id"), nullable=False, index=True)
    name        = Column(Text, nullable=False)
    key_hash    = Column(Text, nullable=False, unique=True, index=True)
    key_prefix  = Column(Text, nullable=False)  # first 8 chars for display
    
    # Permissions
    scopes      = Column(JSON, default=[])  # list of allowed endpoint prefixes
    rate_limit  = Column(Integer, default=1000)  # requests per day
    
    # Usage tracking
    daily_usage = Column(Integer, default=0)
    last_used_at = Column(Text, nullable=True)
    
    # Status
    expires_at  = Column(Text, nullable=True)
    is_active   = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at  = Column(Text, default=datetime.utcnow, nullable=False)
    updated_at  = Column(Text, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_keys")
    usage_logs = relationship("APIUsageLog", back_populates="api_key", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_api_keys_user_id_active", "user_id", "is_active"),
    )


class APIUsageLog(Base):
    __tablename__ = "api_usage_logs"

    id          = Column(Text, primary_key=True)
    api_key_id  = Column(Text, ForeignKey("api_keys.id"), nullable=False, index=True)
    user_id     = Column(Text, ForeignKey("users.id"), nullable=False, index=True)
    
    # Request details
    endpoint    = Column(Text, nullable=False)
    method      = Column(Text, nullable=False)
    status_code = Column(Integer, nullable=False)
    latency_ms  = Column(Integer, nullable=True)
    
    # Size tracking
    request_size  = Column(Integer, nullable=True)
    response_size = Column(Integer, nullable=True)
    
    # Client info
    ip_address  = Column(Text, nullable=True)
    user_agent  = Column(Text, nullable=True)
    
    # Timestamp
    created_at  = Column(Text, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")

    __table_args__ = (
        Index("ix_api_usage_date_endpoint", "created_at", "endpoint"),
    )


class Webhook(Base):
    __tablename__ = "webhooks"

    id          = Column(Text, primary_key=True)
    user_id     = Column(Text, ForeignKey("users.id"), nullable=False, index=True)
    url         = Column(Text, nullable=False)
    events      = Column(JSON, nullable=False)  # list of event types
    secret      = Column(Text, nullable=False)  # for signature verification
    
    # Status
    is_active   = Column(Boolean, default=True, nullable=False)
    last_triggered_at = Column(Text, nullable=True)
    failure_count = Column(Integer, default=0)
    
    # Timestamps
    created_at  = Column(Text, default=datetime.utcnow, nullable=False)
    updated_at  = Column(Text, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id          = Column(Text, primary_key=True)
    webhook_id  = Column(Text, ForeignKey("webhooks.id"), nullable=False, index=True)
    event       = Column(Text, nullable=False)
    payload     = Column(JSON, nullable=False)
    
    # Delivery status
    status      = Column(Text, nullable=False)  # pending, success, failed
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    
    # Retry logic
    attempts    = Column(Integer, default=0)
    next_retry_at = Column(Text, nullable=True)
    
    # Timestamp
    created_at  = Column(Text, default=datetime.utcnow, nullable=False)

    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")
