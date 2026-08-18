import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Text, Integer, Boolean, Float,
    ForeignKey, Index, TIMESTAMP, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base


class TwinCategory(Base):
    __tablename__ = "twin_categories"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name           = Column(Text, unique=True, nullable=False)  # e.g. "Author", "CEO", "Musician"
    slug           = Column(Text, unique=True, nullable=False)  # e.g. "author", "ceo", "musician"
    description    = Column(Text, nullable=True)
    icon           = Column(Text, nullable=True)  # emoji or icon name
    is_active      = Column(Boolean, default=True, nullable=False)
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)


class Twin(Base):
    __tablename__ = "twins"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id       = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id    = Column(UUID(as_uuid=True), ForeignKey("twin_categories.id"), nullable=True)
    
    # Identity
    name           = Column(Text, nullable=False)  # Display name
    slug           = Column(Text, unique=True, nullable=False)  # URL-friendly identifier
    tagline        = Column(Text, nullable=True)  # Short description
    bio            = Column(Text, nullable=True)  # Full biography
    avatar_url     = Column(Text, nullable=True)
    cover_url      = Column(Text, nullable=True)
    
    # Public figure fields
    is_public_figure = Column(Boolean, default=False, nullable=False)
    public_figure_name = Column(Text, nullable=True)  # Real name if different
    
    # Verification & trust
    verification_level = Column(Text, default="unverified", nullable=False)
    # unverified, email_verified, id_verified, official
    
    # Personality & behavior (replaces persona_blob)
    personality_config = Column(JSONB, nullable=True)  # voice, tone, style preferences
    boundaries      = Column(JSONB, nullable=True)  # what the twin won't discuss
    knowledge_anchors = Column(JSONB, nullable=True)  # core facts to always include
    
    # Status
    status          = Column(Text, default="draft", nullable=False)
    # draft, active, archived, suspended
    visibility      = Column(Text, default="private", nullable=False)
    # private, unlisted, public
    
    # Stats (denormalized for performance)
    total_chats     = Column(Integer, default=0, nullable=False)
    total_messages  = Column(Integer, default=0, nullable=False)
    avg_fidelity    = Column(Float, nullable=True)  # average fidelity score
    
    # Metadata
    metadata_       = Column("metadata", JSONB, nullable=True)  # flexible extra data
    
    created_at      = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at      = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)

    # Relationships
    owner           = relationship("User", back_populates="twins")
    category        = relationship("TwinCategory")
    sources         = relationship("Source", back_populates="twin", cascade="all, delete-orphan")
    knowledge_items = relationship("KnowledgeItem", back_populates="twin", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="twin", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_twins_owner_id", "owner_id"),
        Index("ix_twins_category_id", "category_id"),
        Index("ix_twins_slug", "slug"),
        Index("ix_twins_status", "status"),
        Index("ix_twins_visibility", "visibility"),
    )


class Source(Base):
    __tablename__ = "sources"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_id        = Column(UUID(as_uuid=True), ForeignKey("twins.id", ondelete="CASCADE"), nullable=False)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Source info
    source_type    = Column(Text, nullable=False)
    # document, url, interview, manual, whatsapp, social_media
    title          = Column(Text, nullable=True)  # user-provided title
    url            = Column(Text, nullable=True)  # original URL if applicable
    file_key       = Column(Text, nullable=True)  # R2 storage key
    file_name      = Column(Text, nullable=True)  # original filename
    file_size      = Column(Integer, nullable=True)  # bytes
    content_type   = Column(Text, nullable=True)  # MIME type
    
    # Processing status
    status         = Column(Text, default="pending", nullable=False)
    # pending, processing, ready, failed, archived
    error          = Column(Text, nullable=True)
    
    # Stats
    chunk_count    = Column(Integer, default=0, nullable=False)
    
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    twin           = relationship("Twin", back_populates="sources")
    knowledge_items = relationship("KnowledgeItem", back_populates="source", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sources_twin_id", "twin_id"),
        Index("ix_sources_user_id", "user_id"),
        Index("ix_sources_status", "status"),
    )


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_id        = Column(UUID(as_uuid=True), ForeignKey("twins.id", ondelete="CASCADE"), nullable=False)
    source_id      = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    
    # Content
    content_type   = Column(Text, nullable=False)
    # fact, opinion, preference, memory, skill, relationship, event
    content        = Column(Text, nullable=False)  # the actual knowledge
    confidence     = Column(Float, default=1.0, nullable=False)  # 0.0 to 1.0
    
    # Embedding (for semantic search)
    embedding_id   = Column(Text, nullable=True)  # Qdrant point ID
    
    # Metadata
    metadata_      = Column("metadata", JSONB, nullable=True)  # structured data
    
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active      = Column(Boolean, default=True, nullable=False)

    # Relationships
    twin           = relationship("Twin", back_populates="knowledge_items")
    source         = relationship("Source", back_populates="knowledge_items")

    __table_args__ = (
        Index("ix_knowledge_items_twin_id", "twin_id"),
        Index("ix_knowledge_items_source_id", "source_id"),
        Index("ix_knowledge_items_content_type", "content_type"),
    )


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_id        = Column(UUID(as_uuid=True), ForeignKey("twins.id", ondelete="CASCADE"), nullable=False)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session info
    status         = Column(Text, default="active", nullable=False)
    # active, completed, abandoned
    topic          = Column(Text, nullable=True)  # interview focus area
    
    # Progress
    questions_asked = Column(Integer, default=0, nullable=False)
    messages_count  = Column(Integer, default=0, nullable=False)
    
    # Knowledge extracted
    items_extracted = Column(Integer, default=0, nullable=False)
    
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    twin           = relationship("Twin", back_populates="interview_sessions")
    messages       = relationship("InterviewMessage", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_interview_sessions_twin_id", "twin_id"),
        Index("ix_interview_sessions_user_id", "user_id"),
        Index("ix_interview_sessions_status", "status"),
    )


class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id     = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Message content
    role           = Column(Text, nullable=False)  # "interviewer" or "interviewee"
    content        = Column(Text, nullable=False)
    
    # Knowledge extraction
    knowledge_items_extracted = Column(JSONB, nullable=True)  # array of extracted items
    
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    session        = relationship("InterviewSession", back_populates="messages")

    __table_args__ = (
        Index("ix_interview_messages_session_id", "session_id"),
    )


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name           = Column(Text, unique=True, nullable=False)  # e.g. "free", "pro", "enterprise"
    display_name   = Column(Text, nullable=False)  # e.g. "Free", "Pro", "Enterprise"
    description    = Column(Text, nullable=True)
    
    # Limits
    max_twins      = Column(Integer, default=1, nullable=False)
    max_sources_per_twin = Column(Integer, default=5, nullable=False)
    max_messages_per_day = Column(Integer, default=100, nullable=False)
    max_interview_sessions = Column(Integer, default=3, nullable=False)
    
    # Features
    features       = Column(JSONB, nullable=True)  # list of feature flags
    
    # Pricing (for future use)
    price_monthly  = Column(Integer, nullable=True)  # cents
    price_yearly   = Column(Integer, nullable=True)  # cents
    
    is_active      = Column(Boolean, default=True, nullable=False)
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_id        = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    
    # Status
    status         = Column(Text, default="active", nullable=False)
    # active, cancelled, past_due, trial
    
    # Period
    current_period_start = Column(TIMESTAMP(timezone=True), nullable=True)
    current_period_end   = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Usage tracking
    twins_used     = Column(Integer, default=0, nullable=False)
    messages_today = Column(Integer, default=0, nullable=False)
    messages_reset_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user           = relationship("User", back_populates="subscriptions")
    plan           = relationship("SubscriptionPlan")

    __table_args__ = (
        Index("ix_user_subscriptions_user_id", "user_id"),
        Index("ix_user_subscriptions_status", "status"),
        UniqueConstraint("user_id", name="uq_user_subscriptions_user_id"),
    )


class TwinAccessLog(Base):
    __tablename__ = "twin_access_logs"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_id        = Column(UUID(as_uuid=True), ForeignKey("twins.id", ondelete="CASCADE"), nullable=False)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # null for anonymous
    
    # Access info
    action         = Column(Text, nullable=False)  # chat, view_profile, view_knowledge
    ip_address     = Column(Text, nullable=True)
    user_agent     = Column(Text, nullable=True)
    
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_twin_access_logs_twin_id", "twin_id"),
        Index("ix_twin_access_logs_created_at", "created_at"),
    )
