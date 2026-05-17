import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Text, Integer, Boolean,
    ForeignKey, Index, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    __tablename__ = "users"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email          = Column(Text, unique=True, nullable=False)
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    is_active      = Column(Boolean, default=True, nullable=False)

    personas       = relationship("Persona", back_populates="user")
    messages       = relationship("Message", back_populates="user")


class Persona(Base):
    __tablename__ = "personas"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name           = Column(Text, nullable=False)
    persona_blob   = Column(JSONB, nullable=True)   # full persona JSON
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    is_active      = Column(Boolean, default=True, nullable=False)

    user           = relationship("User", back_populates="personas")
    versions       = relationship("PersonaVersion", back_populates="persona")

    __table_args__ = (
        Index("ix_personas_user_id", "user_id"),
    )


class PersonaVersion(Base):
    __tablename__ = "persona_versions"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id     = Column(UUID(as_uuid=True), ForeignKey("personas.id"), nullable=False)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    persona_blob   = Column(JSONB, nullable=True)
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    persona        = relationship("Persona", back_populates="versions")

    __table_args__ = (
        Index("ix_persona_versions_user_id", "user_id"),
        Index("ix_persona_versions_persona_id", "persona_id"),
    )


class Message(Base):
    __tablename__ = "messages"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    persona_id     = Column(UUID(as_uuid=True), ForeignKey("personas.id"), nullable=True)
    role           = Column(Text, nullable=False)   # "user" or "assistant"
    content        = Column(Text, nullable=False)
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    user           = relationship("User", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_user_id", "user_id"),
        Index("ix_messages_created_at", "created_at"),
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message_id     = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    rating         = Column(Integer, nullable=True)   # e.g. 1-5
    comment        = Column(Text, nullable=True)
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_feedback_user_id", "user_id"),
        Index("ix_feedback_created_at", "created_at"),
    )


class PreferencePair(Base):
    __tablename__ = "preference_pairs"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    prompt         = Column(Text, nullable=False)
    chosen         = Column(Text, nullable=False)
    rejected       = Column(Text, nullable=False)
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_preference_pairs_user_id", "user_id"),
    )


class DailyQuestionsAsked(Base):
    __tablename__ = "daily_questions_asked"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question       = Column(Text, nullable=False)
    asked_at       = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_daily_questions_user_id", "user_id"),
    )


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status         = Column(Text, nullable=False, default="pending")  # pending, running, done, failed
    source         = Column(Text, nullable=True)
    error          = Column(Text, nullable=True)
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_ingestion_jobs_user_id", "user_id"),
    )


class VoiceCache(Base):
    __tablename__ = "voice_cache"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id        = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text_hash      = Column(Text, nullable=False)    # hash of the input text
    audio_url      = Column(Text, nullable=False)    # MinIO URL
    created_at     = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_voice_cache_user_id", "user_id"),
        Index("ix_voice_cache_text_hash", "text_hash"),
    )