from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class RetrievedChunk(BaseModel):
    """
    A single chunk returned by PersonaRetriever.search_hybrid().
    This is the frozen contract — do not change without notifying P2.
    """
    model_config = ConfigDict(frozen=True)

    text: str        # Chunk text content
    source: str      # Where it came from e.g. "interview", "whatsapp"
    score: float     # Relevance score (higher = more relevant)


class RetrievalResult(BaseModel):
    """
    Full result returned by search_hybrid().
    Contains top-k chunks for a given query.
    """
    model_config = ConfigDict(frozen=True)

    user_id: str
    query: str
    chunks: list[RetrievedChunk]
    total: int