"""
shared/contracts/voice.py
=========================
Frozen voice API contracts.

Version: 1.0
Frozen: Day 13
Reviewers: P2 (CODEOWNERS)

CHANGES REQUIRE:
  1. New entry in decisions.md
  2. P2 review
  3. Bump version comment above
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


# ── STT (Speech-to-Text) ─────────────────────────────────────────────────────

class TranscribeResponse(BaseModel):
    """
    Response from POST /voice/transcribe.
    Confirmed with P3 on Day 13 sync — frozen.
    """
    text:       str   = Field(..., description="Transcribed text from audio")
    duration_s: float = Field(..., description="Audio duration in seconds")
    audio_id:   str   = Field(..., description="UUID — R2 key prefix for this recording")
    latency_ms: int   = Field(..., description="Total transcription time in milliseconds")


# ── TTS (Text-to-Speech) ─────────────────────────────────────────────────────

class SynthesiseResponse(BaseModel):
    """
    Response from POST /voice/synthesise.
    """
    url:        str   = Field(..., description="Presigned R2 URL to WAV file (valid 1 hour)")
    voice_id:   str   = Field(..., description="Voice model used")
    char_count: int   = Field(..., description="Number of characters synthesised")
    latency_ms: int   = Field(..., description="Total synthesis time in milliseconds")
    cached:     bool  = Field(..., description="True if returned from cache (< 100ms)")


# ── Voices list ───────────────────────────────────────────────────────────────

class VoicesResponse(BaseModel):
    """
    Response from GET /voice/voices.
    """
    voices:  list[str] = Field(..., description="Available voice_id strings")
    default: str       = Field(..., description="Default voice_id")
    total:   int       = Field(..., description="Total number of available voices")


# ── Request models ────────────────────────────────────────────────────────────

class SynthesiseRequest(BaseModel):
    """
    Request body for POST /voice/synthesise (if switching from query params to body).
    """
    text:     str = Field(..., min_length=1, max_length=5000)
    voice_id: str = Field(default="en_US-lessac-medium")