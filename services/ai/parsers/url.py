"""
url.py
======
Parse web pages into Chunk objects using trafilatura.

Features:
    - Fetches URL content
    - Extracts main article text (removes nav/ads/footers)
    - Falls back to empty string on failure — never raises
    - Returns list[Chunk]

Usage:
    chunks = parse_url("https://example.com/article")
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, timezone

import trafilatura

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.contracts.chunk import Chunk


def parse_url(
    url: str,
    source_id: str | None = None,
) -> list[Chunk]:
    """
    Fetch and parse a web page into a single Chunk.

    Args:
        url:       URL to fetch and parse
        source_id: Optional custom source ID (defaults to url)

    Returns:
        list[Chunk] — one chunk with extracted article text,
                      or empty list if fetch/extract fails
    """
    sid = source_id or url

    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return []

        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )

        if not text or len(text.strip()) < 50:
            return []

        return [Chunk(
            text=text.strip(),
            source="url",
            source_id=sid,
            created_at=datetime.now(timezone.utc),
            metadata={"url": url},
        )]

    except Exception:
        # Never raises — graceful fallback
        return []