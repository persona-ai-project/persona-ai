"""
docx.py
=======
Parse Microsoft Word .docx files into Chunk objects using python-docx.

Features:
    - Extracts all paragraphs
    - Skips blank paragraphs
    - Joins all text into one chunk (whole document)
    - Returns list[Chunk]

Usage:
    chunks = parse_docx("document.docx")
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, timezone
from pathlib import Path

import docx as python_docx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.contracts.chunk import Chunk


def parse_docx(
    filepath: str,
    source_id: str | None = None,
) -> list[Chunk]:
    """
    Parse a Word .docx file into Chunks.

    Args:
        filepath:  Path to the .docx file
        source_id: Optional custom source ID (defaults to filename)

    Returns:
        list[Chunk] — one chunk containing the full document text
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {filepath}")

    sid = source_id or path.name
    now = datetime.now(timezone.utc)

    doc = python_docx.Document(str(path))

    # Extract non-blank paragraphs
    paragraphs = [
        p.text.strip()
        for p in doc.paragraphs
        if p.text.strip()
    ]

    if not paragraphs:
        return []

    # Join all paragraphs into full document text
    full_text = "\n\n".join(paragraphs)

    return [Chunk(
        text=full_text,
        source="docx",
        source_id=sid,
        created_at=now,
        metadata={
            "filename": path.name,
            "paragraph_count": len(paragraphs),
        },
    )]