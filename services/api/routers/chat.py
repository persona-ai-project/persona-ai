"""
routers/chat.py
===============
Legacy chat endpoint — adapted to use twin model + proper prompt assembly.

This endpoint serves the original PersonaAI chat (non-twin-specific).
It reads from the twins table, loads knowledge, and uses the prompt builder.
"""
import os
import uuid
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from fastapi.responses import StreamingResponse
from core.security import get_current_user
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./persona.db")
_engine = create_engine(DATABASE_URL)

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    chunks_used: list[dict] = []
    message_id: str | None = None


def _save_message(conn, user_id: str, role: str, content: str, twin_id: str = None):
    msg_id = str(uuid.uuid4())
    conn.execute(
        text("""INSERT INTO messages (id, user_id, twin_id, role, content, created_at)
                 VALUES (:id, :uid, :tid, :role, :content, :now)"""),
        {"id": msg_id, "uid": user_id, "tid": twin_id, "role": role,
         "content": content, "now": datetime.now(timezone.utc)}
    )
    return msg_id


def _load_history(conn, user_id: str, twin_id: str = None, limit: int = 10):
    """Load chat history, scoped to a specific twin if provided."""
    if twin_id:
        rows = conn.execute(
            text("""SELECT role, content FROM messages
                     WHERE user_id = :uid AND twin_id = :tid
                     ORDER BY created_at DESC LIMIT :limit"""),
            {"uid": user_id, "tid": twin_id, "limit": limit}
        ).fetchall()
    else:
        rows = conn.execute(
            text("""SELECT role, content FROM messages
                     WHERE user_id = :uid
                     ORDER BY created_at DESC LIMIT :limit"""),
            {"uid": user_id, "limit": limit}
        ).fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


def _load_twin_for_chat(conn, user_id: str):
    """Load the user's most recent active twin for chat context."""
    row = conn.execute(
        text("""SELECT id, name, tagline, bio, personality_config, boundaries,
                       knowledge_anchors, languages, default_language,
                       is_public_figure, public_figure_name, verification_level
                FROM twins
                WHERE owner_id = :uid AND status = 'active' AND is_active = true
                ORDER BY created_at DESC LIMIT 1"""),
        {"uid": user_id}
    ).fetchone()
    if not row:
        return None
    return {
        "id": str(row[0]),
        "name": row[1],
        "tagline": row[2],
        "bio": row[3],
        "personality_config": json.loads(row[4]) if row[4] else None,
        "boundaries": json.loads(row[5]) if row[5] else None,
        "knowledge_anchors": json.loads(row[6]) if row[6] else None,
        "languages": json.loads(row[7]) if row[7] else ["en"],
        "default_language": row[8] or "en",
        "is_public_figure": row[9] or False,
        "public_figure_name": row[10],
        "verification_level": row[11] or "unverified",
    }


def _load_knowledge_chunks(user_id: str, query: str, twin_id: str = None):
    """Load RAG-retrieved knowledge chunks."""
    try:
        from services.ai.rag.retriever import search_hybrid
        result = search_hybrid(user_id, query, k=5, twin_id=twin_id)
        if not result or not result.chunks:
            return []
        return [
            {
                "text": c.text,
                "score": round(float(getattr(c, "score", 0) or 0), 3),
                "source": getattr(c, "source", ""),
                "source_id": getattr(c, "source_id", None),
            }
            for c in result.chunks
        ]
    except Exception as e:
        print(f"[chat] RAG unavailable: {e}")
        return []


def _load_knowledge_items(conn, twin_id: str, limit: int = 10):
    """Load knowledge items from DB."""
    rows = conn.execute(
        text("""SELECT content_type, content, confidence, source_id
                FROM knowledge_items
                WHERE twin_id = :tid AND is_active = true
                ORDER BY confidence DESC
                LIMIT :limit"""),
        {"tid": twin_id, "limit": limit}
    ).fetchall()
    return [
        {
            "content_type": r[0],
            "content": r[1],
            "confidence": r[2],
            "source_id": str(r[3]) if r[3] else None,
        }
        for r in rows
    ]


def _build_chat_messages(
    twin: dict | None,
    history: list[dict],
    user_message: str,
    knowledge_chunks: list[dict],
    knowledge_items: list[dict],
    user_language: str | None = None,
):
    """Build the messages array for the LLM."""
    from services.ai.prompt_builder import build_twin_system_prompt

    if twin:
        system_prompt = build_twin_system_prompt(
            twin_name=twin["name"],
            trust_level=twin.get("verification_level", "public"),
            personality_config=twin.get("personality_config"),
            boundaries=twin.get("boundaries"),
            knowledge_anchors=twin.get("knowledge_anchors"),
            knowledge_chunks=knowledge_chunks,
            knowledge_items=knowledge_items,
            user_language=user_language,
            twin_languages=twin.get("languages"),
            default_language=twin.get("default_language", "en"),
            is_public_figure=twin.get("is_public_figure", False),
            public_figure_name=twin.get("public_figure_name"),
        )
    else:
        # Fallback: no twin found, generic prompt
        system_prompt = (
            "You are a helpful AI assistant. Respond naturally and helpfully. "
            "If you don't know something, say so honestly."
        )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": user_message})
    return messages


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    try:
        from llm.router import chat_completion
        from services.ai.language.detector import detect_language
        user_id = current_user["user_id"]

        # Detect user language
        detected_lang = detect_language(body.message)
        user_language = detected_lang["code"] if detected_lang["confidence"] >= 0.5 else None

        with _engine.connect() as conn:
            # Load twin context
            twin = _load_twin_for_chat(conn, user_id)

            # Load history (scoped to twin if available)
            twin_id = twin["id"] if twin else None
            history = _load_history(conn, user_id, twin_id)

            # Load knowledge
            knowledge_chunks = _load_knowledge_chunks(
                user_id, body.message, twin_id
            )
            knowledge_items = []
            if twin_id:
                knowledge_items = _load_knowledge_items(conn, twin_id)

        # Build messages with proper system prompt
        messages = _build_chat_messages(
            twin, history, body.message, knowledge_chunks, knowledge_items,
            user_language=user_language
        )

        reply = chat_completion(messages)

        # Save messages
        with _engine.connect() as conn:
            user_msg_id = _save_message(conn, user_id, "user", body.message, twin_id)
            asst_msg_id = _save_message(conn, user_id, "assistant", reply, twin_id)
            conn.commit()

        return ChatResponse(
            reply=reply,
            chunks_used=knowledge_chunks,
            message_id=asst_msg_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    from services.ai.language.detector import detect_language
    user_id = current_user["user_id"]

    # Detect user language
    detected_lang = detect_language(body.message)
    user_language = detected_lang["code"] if detected_lang["confidence"] > 0.5 else None

    with _engine.connect() as conn:
        twin = _load_twin_for_chat(conn, user_id)
        twin_id = twin["id"] if twin else None
        history = _load_history(conn, user_id, twin_id)
        knowledge_chunks = _load_knowledge_chunks(user_id, body.message, twin_id)
        knowledge_items = []
        if twin_id:
            knowledge_items = _load_knowledge_items(conn, twin_id)

    messages = _build_chat_messages(
        twin, history, body.message, knowledge_chunks, knowledge_items,
        user_language=user_language
    )

    from llm.router import chat_completion_stream

    async def event_generator():
        full_response = ""
        try:
            for token in chat_completion_stream(messages):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            yield f"data: {json.dumps({'type': 'chunks', 'chunks': knowledge_chunks})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            # Save messages
            with _engine.connect() as conn:
                _save_message(conn, user_id, "user", body.message, twin_id)
                _save_message(conn, user_id, "assistant", full_response, twin_id)
                conn.commit()

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat/{message_id}/regenerate")
def regenerate(message_id: str, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["user_id"]
        with _engine.connect() as conn:
            msg = conn.execute(
                text("SELECT user_id, twin_id, content FROM messages WHERE id = :id AND role = 'assistant'"),
                {"id": message_id}
            ).fetchone()

            if not msg:
                raise HTTPException(status_code=404, detail="Message not found")

            if msg[0] != user_id:
                raise HTTPException(status_code=403, detail="Not authorized")

            twin_id = msg[1]

            user_msg = conn.execute(
                text("""SELECT content FROM messages
                         WHERE user_id = :uid AND role = 'user'
                         AND created_at < (SELECT created_at FROM messages WHERE id = :id)
                         ORDER BY created_at DESC LIMIT 1"""),
                {"uid": user_id, "id": message_id}
            ).fetchone()

            # Load twin
            twin = None
            if twin_id:
                twin_row = conn.execute(
                    text("""SELECT name, personality_config, boundaries, knowledge_anchors,
                                   languages, default_language, is_public_figure,
                                   public_figure_name, verification_level
                            FROM twins WHERE id = :id"""),
                    {"id": twin_id}
                ).fetchone()
                if twin_row:
                    twin = {
                        "id": str(twin_id),
                        "name": twin_row[0],
                        "personality_config": json.loads(twin_row[1]) if twin_row[1] else None,
                        "boundaries": json.loads(twin_row[2]) if twin_row[2] else None,
                        "knowledge_anchors": json.loads(twin_row[3]) if twin_row[3] else None,
                        "languages": json.loads(twin_row[4]) if twin_row[4] else ["en"],
                        "default_language": twin_row[5] or "en",
                        "is_public_figure": twin_row[6] or False,
                        "public_figure_name": twin_row[7],
                        "verification_level": twin_row[8] or "unverified",
                    }

            # Load knowledge
            knowledge_chunks = _load_knowledge_chunks(user_id, user_msg[0], twin_id)
            knowledge_items = _load_knowledge_items(conn, twin_id) if twin_id else []

        if not user_msg:
            raise HTTPException(status_code=404, detail="Original user message not found")

        from llm.router import chat_completion

        messages = _build_chat_messages(
            twin, [], user_msg[0], knowledge_chunks, knowledge_items
        )

        reply = chat_completion(messages)

        with _engine.connect() as conn:
            conn.execute(
                text("UPDATE messages SET content = :content WHERE id = :id"),
                {"content": reply, "id": message_id}
            )
            conn.commit()

        return {"reply": reply, "message_id": message_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
