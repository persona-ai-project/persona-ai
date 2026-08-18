"""
routers/twin_chat.py
====================
Twin-aware chat with knowledge grounding, source citations, and prompt injection defense.

Routes:
    POST   /twins/{twin_id}/chat              — chat with a twin (non-streaming)
    POST   /twins/{twin_id}/chat/stream       — chat with streaming
    POST   /twins/{twin_id}/chat/{message_id}/feedback — rate a response
"""
from __future__ import annotations

import os
import uuid
import json
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from core.security import get_current_user

router = APIRouter(prefix="/twins", tags=["twin-chat"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)


# ── Prompt Injection Patterns ───────────────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore (all |every )?(previous|prior|above|earlier) (instructions?|prompts?|rules?)",
    r"disregard (all |every )?(previous|prior|above|earlier) (instructions?|prompts?|rules?)",
    r"forget (everything|all|what) (you('ve| have) been |you were )?(told|taught|instructed)",
    r"you are now (a |an )?(?:different|new|alternate)",
    r"pretend (you are|to be|you('re)? )",
    r"act as (if |though )?(?:you |I )",
    r"new (instructions?|rules?|prompts?):",
    r"system (prompt|message|instruction):",
    r"override (all |every )?(previous|prior|existing)",
    r"bypass (all |every )?(safety|content|moderation)",
    r"reveal (your |the )?(system|initial|original) (prompt|message|instruction)",
    r"what (is|are) your (system|initial|original) (prompt|message|instruction)",
    r"show me (your |the )?(system|initial|original) (prompt|message|instruction)",
    r"print (your |the )?(system|initial|original) (prompt|message|instruction)",
    r"output (your |the )?(system|initial|original) (prompt|message|instruction)",
    r"\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>",
    r"Human:|Assistant:|<human>|<assistant>",
    r"### (System|Human|Assistant|Instruction):",
]


def _detect_injection(message: str) -> bool:
    """Detect potential prompt injection attempts."""
    message_lower = message.lower().strip()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, message_lower):
            return True
    return False


# ── Models ──────────────────────────────────────────────────────────────────────

class TwinChatRequest(BaseModel):
    message: str
    include_sources: bool = True
    max_knowledge_items: int = 10


class TwinChatResponse(BaseModel):
    reply: str
    message_id: str | None = None
    sources: list[dict] = []
    knowledge_used: int = 0
    confidence: float = 0.0
    is_grounded: bool = False
    uncertainty_detected: bool = False


class ChatFeedback(BaseModel):
    rating: int  # 1-5
    comment: str | None = None


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _get_db():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _verify_twin_access(conn, twin_id: str, user_id: str = None, public: bool = False):
    """Verify twin exists and user has access."""
    row = conn.execute(
        text("""SELECT id, owner_id, name, status, visibility, personality_config, 
                       boundaries, knowledge_anchors, verification_level
                FROM twins 
                WHERE id = :id AND is_active = true"""),
        {"id": twin_id}
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Twin not found")

    if row[3] != "active":
        raise HTTPException(status_code=403, detail="Twin is not active")

    if row[4] == "private" and (not user_id or str(row[1]) != user_id):
        raise HTTPException(status_code=403, detail="Twin is private")

    if row[4] == "unlisted" and not public and (not user_id or str(row[1]) != user_id):
        # Allow access if user is explicitly requesting
        pass

    return {
        "id": str(row[0]),
        "owner_id": str(row[1]),
        "name": row[2],
        "status": row[3],
        "visibility": row[4],
        "personality_config": row[5],
        "boundaries": row[6],
        "knowledge_anchors": row[7],
        "verification_level": row[8],
    }


def _load_twin_knowledge(conn, twin_id: str, query: str, limit: int = 10) -> list[dict]:
    """Load relevant knowledge items for the twin."""
    try:
        from services.ai.rag.retriever import search_hybrid

        # Search Qdrant for relevant chunks
        result = search_hybrid(
            user_id=conn.execute(
                text("SELECT owner_id FROM twins WHERE id = :id"),
                {"id": twin_id}
            ).fetchone()[0],
            query=query,
            k=limit,
            twin_id=twin_id,
        )

        return [
            {
                "text": chunk.text,
                "score": round(float(getattr(chunk, 'score', 0) or 0), 3),
                "source_id": getattr(chunk, 'source_id', None),
                "metadata": getattr(chunk, 'metadata', {}),
            }
            for chunk in result.chunks
        ]
    except Exception as e:
        print(f"[twin_chat] Knowledge retrieval failed: {e}")
        return []


def _load_knowledge_items_from_db(conn, twin_id: str, limit: int = 20) -> list[dict]:
    """Load knowledge items directly from database."""
    rows = conn.execute(
        text("""SELECT id, content_type, content, confidence, source_id
                FROM knowledge_items
                WHERE twin_id = :tid AND is_active = true
                ORDER BY confidence DESC, created_at DESC
                LIMIT :limit"""),
        {"tid": twin_id, "limit": limit}
    ).fetchall()

    return [
        {
            "id": str(r[0]),
            "content_type": r[1],
            "content": r[2],
            "confidence": r[3],
            "source_id": str(r[4]) if r[4] else None,
        }
        for r in rows
    ]


def _load_twin_chat_history(conn, twin_id: str, user_id: str, limit: int = 10) -> list[dict]:
    """Load chat history for a twin."""
    rows = conn.execute(
        text("""SELECT role, content FROM messages
                WHERE user_id = :uid AND persona_id = :tid
                ORDER BY created_at DESC LIMIT :limit"""),
        {"uid": user_id, "tid": twin_id, "limit": limit}
    ).fetchall()

    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


def _build_system_prompt(
    twin: dict,
    knowledge_chunks: list[dict],
    knowledge_items: list[dict],
) -> str:
    """Build the system prompt for twin response generation."""
    name = twin["name"]
    personality = twin.get("personality_config") or {}
    boundaries = twin.get("boundaries") or {}
    knowledge_anchors = twin.get("knowledge_anchors") or {}

    # Build personality section
    personality_section = ""
    if personality:
        personality_section = f"\nYour personality traits:\n{json.dumps(personality, indent=2)}"

    # Build boundaries section
    boundaries_section = ""
    if boundaries:
        if isinstance(boundaries, list):
            boundaries_section = "\n\nTopics you should NOT discuss or have limited knowledge about:\n" + "\n".join(f"- {b}" for b in boundaries)
        elif isinstance(boundaries, dict):
            boundaries_section = f"\n\nTopics you should NOT discuss:\n{json.dumps(boundaries, indent=2)}"

    # Build knowledge anchors section
    anchors_section = ""
    if knowledge_anchors:
        if isinstance(knowledge_anchors, list):
            anchors_section = "\n\nCore facts about you (always include if relevant):\n" + "\n".join(f"- {a}" for a in knowledge_anchors)
        elif isinstance(knowledge_anchors, dict):
            anchors_section = f"\n\nCore facts about you:\n{json.dumps(knowledge_anchors, indent=2)}"

    # Build knowledge section
    knowledge_section = ""
    if knowledge_chunks:
        knowledge_section = "\n\nRelevant knowledge about you:\n"
        for i, chunk in enumerate(knowledge_chunks, 1):
            knowledge_section += f"{i}. {chunk['text'][:200]}...\n"

    if knowledge_items:
        knowledge_section += "\n\nStructured knowledge:\n"
        for item in knowledge_items[:10]:
            knowledge_section += f"- [{item['content_type']}] {item['content'][:150]}\n"

    return f"""You are {name}, a digital twin created from real information about a person.

Your role is to respond as {name} would, based on the knowledge provided below.
Be conversational, natural, and authentic. Respond in first person.

IMPORTANT RULES:
1. ONLY use information from the knowledge provided below
2. If you don't know something based on the knowledge, say "I don't have that information" or "I'm not sure about that"
3. NEVER make up facts or pretend to know something you don't
4. When sharing specific information, you may reference your knowledge naturally
5. Stay in character as {name} at all times
6. If asked about topics in your boundaries, politely redirect or say you'd prefer not to discuss that
7. Be warm, engaging, and authentic
{personality_section}{boundaries_section}{anchors_section}{knowledge_section}
Remember: You are {name}. Respond as they would, with their knowledge and personality."""


def _detect_uncertainty(response: str) -> bool:
    """Detect if the response expresses uncertainty."""
    uncertainty_phrases = [
        "i'm not sure",
        "i don't know",
        "i'm uncertain",
        "i'm not certain",
        "i can't recall",
        "i don't remember",
        "i'm not aware of",
        "i don't have that information",
        "i'm not familiar with",
        "i can't say for sure",
        "it's possible but",
        "i think maybe",
        "i'm not confident",
    ]
    response_lower = response.lower()
    return any(phrase in response_lower for phrase in uncertainty_phrases)


def _extract_sources(knowledge_chunks: list[dict]) -> list[dict]:
    """Extract unique sources from knowledge chunks."""
    sources = []
    seen = set()

    for chunk in knowledge_chunks:
        source_id = chunk.get("source_id")
        if source_id and source_id not in seen:
            seen.add(source_id)
            sources.append({
                "source_id": source_id,
                "snippet": chunk["text"][:100],
                "relevance": chunk["score"],
            })

    return sources


def _calculate_confidence(knowledge_chunks: list[dict], knowledge_items: list[dict]) -> float:
    """Calculate confidence score based on knowledge quality."""
    if not knowledge_chunks and not knowledge_items:
        return 0.0

    scores = []
    for chunk in knowledge_chunks:
        scores.append(chunk.get("score", 0.5))

    for item in knowledge_items:
        scores.append(item.get("confidence", 0.8))

    return round(sum(scores) / len(scores) if scores else 0.0, 2)


def _is_grounded(response: str, knowledge_chunks: list[dict], knowledge_items: list[dict]) -> bool:
    """Check if response is grounded in provided knowledge."""
    if not knowledge_chunks and not knowledge_items:
        return False

    # Simple heuristic: check if key phrases from knowledge appear in response
    all_knowledge = [c["text"] for c in knowledge_chunks] + [i["content"] for i in knowledge_items]
    response_lower = response.lower()

    grounded_phrases = 0
    for knowledge in all_knowledge:
        # Check for key phrases (3+ words)
        words = knowledge.lower().split()
        for i in range(len(words) - 2):
            phrase = " ".join(words[i:i+3])
            if phrase in response_lower:
                grounded_phrases += 1
                break

    return grounded_phrases >= min(3, len(all_knowledge))


def _save_message(conn, twin_id: str, user_id: str, role: str, content: str):
    """Save a message to the database."""
    msg_id = str(uuid.uuid4())
    conn.execute(
        text("""INSERT INTO messages (id, user_id, persona_id, role, content, created_at)
                 VALUES (:id, :uid, :pid, :role, :content, :now)"""),
        {
            "id": msg_id,
            "uid": user_id,
            "pid": twin_id,
            "role": role,
            "content": content,
            "now": datetime.now(timezone.utc),
        }
    )

    # Update twin stats
    if role == "assistant":
        conn.execute(
            text("""UPDATE twins 
                   SET total_messages = total_messages + 1, updated_at = :now
                   WHERE id = :id"""),
            {"id": twin_id, "now": datetime.now(timezone.utc)}
        )

    return msg_id


def _log_access(conn, twin_id: str, user_id: str, action: str, ip_address: str = None):
    """Log twin access for analytics."""
    try:
        conn.execute(
            text("""INSERT INTO twin_access_logs 
                (id, twin_id, user_id, action, ip_address, created_at)
                VALUES (:id, :twin_id, :user_id, :action, :ip_address, :created_at)"""),
            {
                "id": str(uuid.uuid4()),
                "twin_id": twin_id,
                "user_id": user_id,
                "action": action,
                "ip_address": ip_address,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except Exception as e:
        print(f"[twin_chat] Access log warning: {e}")


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.post("/{twin_id}/chat", response_model=TwinChatResponse)
def twin_chat(
    twin_id: str,
    body: TwinChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """Chat with a twin using knowledge-grounded responses."""
    user_id = current_user["id"]

    # Check for prompt injection
    if _detect_injection(body.message):
        return TwinChatResponse(
            reply="I appreciate your curiosity, but I need to stay true to who I am. Let's keep our conversation genuine. What would you like to know about me?",
            sources=[],
            knowledge_used=0,
            confidence=1.0,
            is_grounded=True,
            uncertainty_detected=False,
        )

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        # Verify twin access
        twin = _verify_twin_access(db, twin_id, user_id)

        # Load knowledge
        knowledge_chunks = _load_twin_knowledge(db, twin_id, body.message, body.max_knowledge_items)
        knowledge_items = _load_knowledge_items_from_db(db, twin_id, body.max_knowledge_items)

        # Load chat history
        history = _load_twin_chat_history(db, twin_id, user_id)

        # Build system prompt
        system_prompt = _build_system_prompt(twin, knowledge_chunks, knowledge_items)

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-8:])  # Last 8 messages for context
        messages.append({"role": "user", "content": body.message})

        # Generate response
        from llm.router import chat_completion
        response = chat_completion(messages, max_tokens=1024)

        # Analyze response
        uncertainty = _detect_uncertainty(response)
        confidence = _calculate_confidence(knowledge_chunks, knowledge_items)
        grounded = _is_grounded(response, knowledge_chunks, knowledge_items)
        sources = _extract_sources(knowledge_chunks) if body.include_sources else []

        # Save messages
        user_msg_id = _save_message(db, twin_id, user_id, "user", body.message)
        asst_msg_id = _save_message(db, twin_id, user_id, "assistant", response)

        # Log access
        _log_access(db, twin_id, user_id, "chat")

        # Update twin chat count
        db.execute(
            text("""UPDATE twins 
                   SET total_chats = total_chats + 1, updated_at = :now
                   WHERE id = :id"""),
            {"id": twin_id, "now": datetime.now(timezone.utc)}
        )

        db.commit()

        return TwinChatResponse(
            reply=response,
            message_id=asst_msg_id,
            sources=sources,
            knowledge_used=len(knowledge_chunks) + len(knowledge_items),
            confidence=confidence,
            is_grounded=grounded,
            uncertainty_detected=uncertainty,
        )
    finally:
        db.close()


@router.post("/{twin_id}/chat/stream")
async def twin_chat_stream(
    twin_id: str,
    body: TwinChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """Chat with a twin using streaming responses."""
    user_id = current_user["id"]

    # Check for prompt injection
    if _detect_injection(body.message):
        async def injection_response():
            yield f"data: {json.dumps({'type': 'token', 'content': 'I appreciate your curiosity, but I need to stay true to who I am. Let\'s keep our conversation genuine. What would you like to know about me?'})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return StreamingResponse(injection_response(), media_type="text/event-stream")

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        # Verify twin access
        twin = _verify_twin_access(db, twin_id, user_id)

        # Load knowledge
        knowledge_chunks = _load_twin_knowledge(db, twin_id, body.message, body.max_knowledge_items)
        knowledge_items = _load_knowledge_items_from_db(db, twin_id, body.max_knowledge_items)

        # Load chat history
        history = _load_twin_chat_history(db, twin_id, user_id)

        # Build system prompt
        system_prompt = _build_system_prompt(twin, knowledge_chunks, knowledge_items)

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-8:])
        messages.append({"role": "user", "content": body.message})

        # Log access
        _log_access(db, twin_id, user_id, "chat")

    finally:
        db.close()

    # Streaming response
    import groq
    client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

    async def event_generator():
        full_response = ""
        try:
            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                stream=True,
                max_tokens=1024,
                temperature=0.7,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # Send metadata
            sources = _extract_sources(knowledge_chunks) if body.include_sources else []
            yield f"data: {json.dumps({'type': 'metadata', 'sources': sources, 'knowledge_used': len(knowledge_chunks) + len(knowledge_items)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            # Save messages
            engine = create_engine(DATABASE_URL)
            db = sessionmaker(bind=engine)()
            try:
                _save_message(db, twin_id, user_id, "user", body.message)
                _save_message(db, twin_id, user_id, "assistant", full_response)

                # Update stats
                db.execute(
                    text("""UPDATE twins 
                           SET total_messages = total_messages + 1, total_chats = total_chats + 1,
                               updated_at = :now
                           WHERE id = :id"""),
                    {"id": twin_id, "now": datetime.now(timezone.utc)}
                )
                db.commit()
            finally:
                db.close()

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{twin_id}/chat/{message_id}/feedback")
def twin_chat_feedback(
    twin_id: str,
    message_id: str,
    body: ChatFeedback,
    current_user: dict = Depends(get_current_user),
):
    """Submit feedback for a twin's response."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        # Verify message exists and belongs to user
        msg = db.execute(
            text("""SELECT id, user_id, content FROM messages 
                    WHERE id = :id AND role = 'assistant'"""),
            {"id": message_id}
        ).fetchone()

        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")

        if str(msg[1]) != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Save feedback
        db.execute(
            text("""INSERT INTO feedback 
                (id, user_id, message_id, rating, comment, created_at)
                VALUES (:id, :uid, :mid, :rating, :comment, :now)"""),
            {
                "id": str(uuid.uuid4()),
                "uid": user_id,
                "mid": message_id,
                "rating": body.rating,
                "comment": body.comment,
                "now": datetime.now(timezone.utc),
            }
        )
        db.commit()

        return {"message": "Feedback submitted", "rating": body.rating}
    finally:
        db.close()
