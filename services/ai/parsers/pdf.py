"""
pdf.py
======
Parse PDF files into Chunk objects using pypdf.

Features:
    - Extracts text page by page
    - Skips pages with under 50 chars (scanned/empty pages)
    - One Chunk per page
    - Returns list[Chunk]

Usage:
    chunks = parse_pdf("document.pdf")
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, timezone
from pathlib import Path

import pypdf

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.contracts.chunk import Chunk

MIN_PAGE_CHARS = 50  # skip pages shorter than this


def parse_pdf(
    filepath: str,
    source_id: str | None = None,
) -> list[Chunk]:
    """
    Parse a PDF file into Chunks, one per page.

    Args:
        filepath:  Path to the PDF file
        source_id: Optional custom source ID (defaults to filename)

    Returns:
        list[Chunk] — one chunk per non-empty page
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {filepath}")

    sid = source_id or path.name
    chunks: list[Chunk] = []
    now = datetime.now(timezone.utc)

    reader = pypdf.PdfReader(str(path))
    total_pages = len(reader.pages)

    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        text = text.strip()

        # Skip empty or nearly empty pages (scanned images, blank pages)
        if len(text) < MIN_PAGE_CHARS:
            continue

        chunks.append(Chunk(
            text=text,
            source="pdf",
            source_id=sid,
            created_at=now,
            metadata={
                "page": page_num,
                "total_pages": total_pages,
                "filename": path.name,
            },
        ))

    return chunks