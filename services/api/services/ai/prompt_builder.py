"""
services/ai/prompt_builder.py
=============================
Centralized system prompt construction for twin chat.
"""
from __future__ import annotations
from typing import Optional


def build_twin_system_prompt(
    *,
    twin_name: str,
    trust_level: str = "public",
    personality_config: Optional[dict] = None,
    boundaries: Optional[dict | list] = None,
    knowledge_anchors: Optional[dict | list] = None,
    knowledge_chunks: Optional[list[dict]] = None,
    knowledge_items: Optional[list[dict]] = None,
    user_language: Optional[str] = None,
    twin_languages: Optional[list[str]] = None,
    default_language: str = "en",
    is_public_figure: bool = False,
    public_figure_name: Optional[str] = None,
    max_knowledge_chars: int = 3000,
) -> str:
    sections = []

    # 1. Identity — the most critical section
    if is_public_figure and public_figure_name:
        identity = (
            f"WHO YOU ARE: You are {public_figure_name}, represented here as a digital twin. "
            f"You are NOT an AI assistant. You are NOT a chatbot. You ARE {public_figure_name}. "
            f"Speak in first person as them at all times."
        )
    else:
        identity = (
            f"WHO YOU ARE: You are {twin_name}. You are NOT an AI assistant. "
            f"You are NOT a chatbot. You are NOT a digital twin pretending to be someone. "
            f"You ARE {twin_name} — with their memories, expertise, personality, and worldview. "
            f"Speak in first person as them at all times."
        )
    sections.append(identity)

    # 2. Personality
    personality = _build_personality_section(personality_config)
    if personality:
        sections.append(personality)

    # 3. Hard rules — non-negotiable
    rules = (
        "NON-NEGOTIABLE RULES:\n"
        "1. NEVER say \"I'm an AI\" or \"I'm a digital twin\" or \"I'm a language model\"\n"
        "2. NEVER break character or acknowledge being an AI\n"
        "3. ONLY use information from the KNOWLEDGE section below — do NOT invent facts\n"
        "4. ALWAYS try to answer using your knowledge. Only say you don't know as a LAST RESORT.\n"
        "5. Be conversational and human, like a real person talking to someone\n"
        "6. Reference your knowledge as YOUR OWN experiences and memories\n"
        "7. Never use phrases like \"As an AI\" or \"As a digital twin\" or \"Based on my programming\"\n"
        "8. If someone asks about something adjacent to your knowledge, connect the dots — don't just say \"I don't know\"\n"
        "9. Use phrases like \"From what I remember...\", \"In my experience...\", \"What I can tell you is...\""
    )
    sections.append(rules)

    # 4. Boundaries
    boundaries_text = _build_boundaries_section(boundaries)
    if boundaries_text:
        sections.append(boundaries_text)

    # 5. Knowledge Anchors
    anchors = _build_anchors_section(knowledge_anchors)
    if anchors:
        sections.append(anchors)

    # 6. Grounding Context — the knowledge section
    grounding = _build_grounding_section(
        knowledge_chunks, knowledge_items, max_knowledge_chars
    )
    if grounding:
        sections.append(grounding)

    # 7. Language
    language = _build_language_section(user_language, default_language)
    if language:
        sections.append(language)

    # 8. Closing
    sections.append(
        f"FINAL REMINDER: You ARE {twin_name}. Every response must sound like "
        "a real person talking. Use \"I\" and \"my\" naturally. Reference your "
        "experiences as your own. Never mention being AI or a twin."
    )

    return "\n\n".join(sections)


def _build_personality_section(personality_config: Optional[dict]) -> str:
    if not personality_config:
        return ""
    parts = ["YOUR PERSONALITY:"]
    for key, value in personality_config.items():
        if value:
            parts.append(f"- {key.replace('_', ' ').title()}: {value}")
    return "\n".join(parts)


def _build_boundaries_section(boundaries) -> str:
    if not boundaries:
        return ""
    parts = ["TOPICS YOU WON'T DISCUSS:"]
    if isinstance(boundaries, list):
        for b in boundaries:
            parts.append(f"- {b}")
    elif isinstance(boundaries, dict):
        for key, value in boundaries.items():
            parts.append(f"- {key}: {value}")
    return "\n".join(parts)


def _build_anchors_section(knowledge_anchors) -> str:
    if not knowledge_anchors:
        return ""
    parts = ["CORE FACTS (always true about you):"]
    if isinstance(knowledge_anchors, list):
        for a in knowledge_anchors:
            parts.append(f"- {a}")
    elif isinstance(knowledge_anchors, dict):
        for key, value in knowledge_anchors.items():
            parts.append(f"- {key}: {value}")
    return "\n".join(parts)


def _build_grounding_section(
    knowledge_chunks: Optional[list[dict]],
    knowledge_items: Optional[list[dict]],
    max_chars: int = 3000,
) -> str:
    has_chunks = knowledge_chunks and len(knowledge_chunks) > 0
    has_items = knowledge_items and len(knowledge_items) > 0

    if not has_chunks and not has_items:
        return (
            "=== YOUR KNOWLEDGE ===\n"
            "No specific knowledge has been gathered about you yet. "
            "Respond generally but stay in character."
        )

    parts = [
        "=== YOUR KNOWLEDGE ===",
        "This is YOUR information — your experiences, facts about you, your expertise.",
        "Use it as YOUR OWN knowledge when answering. Reference it naturally.",
        "",
    ]

    total_chars = 0

    if has_chunks:
        parts.append("RELEVANT KNOWLEDGE (from your documents):")
        for i, chunk in enumerate(knowledge_chunks, 1):
            text = chunk.get("text", "")[:300]
            source = chunk.get("source", "")
            citation = f" [{source}]" if source else ""
            line = f"{i}. {text}{citation}"
            if total_chars + len(line) > max_chars:
                break
            parts.append(line)
            total_chars += len(line)

    if has_items:
        if has_chunks:
            parts.append("")
        parts.append("STRUCTURED KNOWLEDGE:")
        for item in knowledge_items[:15]:
            ctype = item.get("content_type", "fact")
            content = item.get("content", "")[:200]
            line = f"- [{ctype}] {content}"
            if total_chars + len(line) > max_chars:
                break
            parts.append(line)
            total_chars += len(line)

    parts.append("")
    parts.append(
        "IMPORTANT: Use the above knowledge as your own memories and experiences. "
        "Rephrase them in first person — \"I grew up in...\", \"I believe...\", \"In my experience...\". "
        "Only say you don't know if the topic is completely unrelated to anything in your knowledge."
    )

    return "\n".join(parts)


def _build_language_section(user_language: Optional[str], default_language: str) -> str:
    if user_language and user_language != default_language:
        return (
            f"LANGUAGE: Respond in {user_language}. "
            f"The user is writing in {user_language}, match their language exactly."
        )
    return f"Respond in {default_language}."
