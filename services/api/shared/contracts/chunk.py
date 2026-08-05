from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class Chunk(BaseModel):
    """
    Immutable contract for a text chunk passing through the ingestion pipeline.
    Frozen so chunks cannot be mutated mid-flight.
    """
    model_config = ConfigDict(frozen=True)

    text: str
    source: str
    source_id: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkList(BaseModel):
    """Wrapper for a list of chunks — used in API responses."""
    model_config = ConfigDict(frozen=True)

    chunks: list[Chunk]
    total: int
