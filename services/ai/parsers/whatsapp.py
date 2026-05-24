"""
whatsapp.py
===========
Parse WhatsApp exported .txt chat files into Chunk objects.

WhatsApp export format (varies by region):
    [DD/MM/YY, HH:MM:SS] Name: Message
    MM/DD/YY, HH:MM - Name: Message

Features:
    - Handles multi-line messages (continuation lines)
    - Filters to owner messages only
    - Skips system messages
    - Flexible date parsing via dateutil
    - Returns list[Chunk]

Usage:
    chunks = parse_whatsapp("chat.txt", owner_name="John")
"""
from __future__ import annotations

import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

from dateutil import parser as dateutil_parser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.contracts.chunk import Chunk

# Matches WhatsApp timestamp lines (various formats)
MSG_PATTERN = re.compile(
    r'^\[?(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}),?\s'
    r'(\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AP]M)?)\]?\s[-–]\s'
    r'(.+?):\s(.+)$',
    re.IGNORECASE
)

# System messages to skip
SYSTEM_MESSAGES = [
    "messages and calls are end-to-end encrypted",
    "missed voice call",
    "missed video call",
    "you deleted this message",
    "this message was deleted",
    "changed the subject",
    "changed this group",
    "added you",
    "left",
    "joined using this group",
]


def _is_system_message(text: str) -> bool:
    text_lower = text.lower().strip()
    return any(sys_msg in text_lower for sys_msg in SYSTEM_MESSAGES)


def parse_whatsapp(
    filepath: str,
    owner_name: str,
    source_id: str | None = None,
) -> list[Chunk]:
    """
    Parse a WhatsApp exported .txt file.

    Args:
        filepath:   Path to the exported .txt file
        owner_name: Name of the person whose messages to extract
        source_id:  Optional custom source ID (defaults to filename)

    Returns:
        list[Chunk] — one chunk per message from owner_name
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"WhatsApp file not found: {filepath}")

    sid = source_id or path.name
    chunks: list[Chunk] = []

    current_date: datetime | None = None
    current_sender: str | None = None
    current_lines: list[str] = []

    def flush():
        """Save accumulated message lines as a Chunk if from owner."""
        nonlocal current_lines, current_sender, current_date
        if not current_lines or not current_sender:
            return
        text = " ".join(current_lines).strip()
        if (
            current_sender.strip().lower() == owner_name.strip().lower()
            and text
            and not _is_system_message(text)
            and len(text) >= 3
        ):
            chunks.append(Chunk(
                text=text,
                source="whatsapp",
                source_id=sid,
                created_at=current_date or datetime.now(timezone.utc),
                metadata={"sender": current_sender},
            ))
        current_lines = []

    with open(filepath, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            match = MSG_PATTERN.match(line)
            if match:
                flush()  # save previous message
                date_str, time_str, sender, message = match.groups()
                try:
                    current_date = dateutil_parser.parse(
                        f"{date_str} {time_str}"
                    ).replace(tzinfo=timezone.utc)
                except Exception:
                    current_date = datetime.now(timezone.utc)
                current_sender = sender.strip()
                current_lines = [message.strip()]
            else:
                # Continuation line — append to current message
                stripped = line.strip()
                if stripped and current_lines is not None:
                    current_lines.append(stripped)

    flush()  # save last message
    return chunks