"""
markdown.py
===========
Parse Markdown (.md) files into Chunk objects.

Features:
    - Simple file read
    - One chunk per file
    - Returns list[Chunk]

Usage:
    chunks = parse_markdown("notes.md")
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.contracts.chunk import Chunk


def parse_markdown(
    filepath: str,
    source_id: str | None = None,
) -> list[Chunk]:
    """
    Parse a Markdown file into a single Chunk.

    Args:
        filepath:  Path to the .md file
        source_id: Optional custom source ID (defaults to filename)

    Returns:
        list[Chunk] — one chunk with full file content
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {filepath}")

    sid = source_id or path.name
    text = path.read_text(encoding="utf-8", errors="replace").strip()

    if not text:
        return []

    return [Chunk(
        text=text,
        source="markdown",
        source_id=sid,
        created_at=datetime.now(timezone.utc),
        metadata={"filename": path.name},
    )]