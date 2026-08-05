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

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/persona")
_engine = create_engine(DATABASE_URL)

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    chunks_used: list[dict] = []
    message_id: str | None = None


def _save_message(conn, user_id: str, role: str, content: str, persona_id: str = None):
    msg_id = str(uuid.uuid4())
    conn.execute(
        text("""INSERT INTO messages (id, user_id, persona_id, role, content, created_at)
                 VALUES (:id, :uid, :pid, :role, :content, :now)"""),
        {"id": msg_id, "uid": user_id, "pid": persona_id, "role": role, "content": content, "now": datetime.now(timezone.utc)}
    )
    return msg_id


def _load_history(conn, user_id: str, limit: int = 20):
    rows = conn.execute(
        text("""SELECT role, content FROM messages
                 WHERE user_id = :uid
                 ORDER BY created_at DESC LIMIT :limit"""),
        {"uid": user_id, "limit": limit}
    ).fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    try:
        from services.ai.rag.retriever import search_hybrid
        from llm.router import chat_completion

        with _engine.connect() as conn:
            history = _load_history(conn, body.user_id)
            persona_row = conn.execute(
                text("SELECT persona_blob FROM personas WHERE user_id = :uid AND is_active = true ORDER BY created_at DESC LIMIT 1"),
                {"uid": body.user_id}
            ).fetchone()

        persona_text = ""
        if persona_row and persona_row[0]:
            blob = persona_row[0]
            if isinstance(blob, str):
                blob = json.loads(blob)
            persona_text = json.dumps(blob, indent=2)

        result = search_hybrid(body.user_id, body.message, k=5)

        chunks_for_response = []
        memory_lines = []
        for chunk in result.chunks:
            score = getattr(chunk, 'score', None) or getattr(chunk, 'scoredense', 0)
            chunks_for_response.append({"text": chunk.text, "score": round(float(score), 3) if score else 0})
            memory_lines.append(f"- {chunk.text}")

        memory_block = "\n".join(memory_lines)

        messages = [
            {"role": "system", "content": f"You are an AI twin of a real person. Respond in first person naturally.\n\nPersona profile:\n{persona_text}"},
        ]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": f"Relevant memories:\n{memory_block}\n\nUser: {body.message}" if memory_block else body.message})

        reply = chat_completion(messages)

        with _engine.connect() as conn:
            persona_id = None
            if persona_row:
                pid_row = conn.execute(
                    text("SELECT id FROM personas WHERE user_id = :uid AND is_active = true ORDER BY created_at DESC LIMIT 1"),
                    {"uid": body.user_id}
                ).fetchone()
                if pid_row:
                    persona_id = str(pid_row[0])

            user_msg_id = _save_message(conn, body.user_id, "user", body.message, persona_id)
            asst_msg_id = _save_message(conn, body.user_id, "assistant", reply, persona_id)
            conn.commit()

        return ChatResponse(reply=reply, chunks_used=chunks_for_response, message_id=asst_msg_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    from services.ai.rag.retriever import search_hybrid

    with _engine.connect() as conn:
        history = _load_history(conn, body.user_id)
        persona_row = conn.execute(
            text("SELECT persona_blob FROM personas WHERE user_id = :uid AND is_active = true ORDER BY created_at DESC LIMIT 1"),
            {"uid": body.user_id}
        ).fetchone()

    persona_text = ""
    if persona_row and persona_row[0]:
        blob = persona_row[0]
        if isinstance(blob, str):
            blob = json.loads(blob)
        persona_text = json.dumps(blob, indent=2)

    result = search_hybrid(body.user_id, body.message, k=5)

    chunks_data = []
    memory_lines = []
    for chunk in result.chunks:
        score = getattr(chunk, 'score', None) or getattr(chunk, 'scoredense', 0)
        chunks_data.append({"text": chunk.text, "score": round(float(score), 3) if score else 0})
        memory_lines.append(f"- {chunk.text}")

    memory_block = "\n".join(memory_lines)

    messages = [
        {"role": "system", "content": f"You are an AI twin of a real person. Respond in first person naturally.\n\nPersona profile:\n{persona_text}"},
    ]
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": f"Relevant memories:\n{memory_block}\n\nUser: {body.message}" if memory_block else body.message})

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

            yield f"data: {json.dumps({'type': 'chunks', 'chunks': chunks_data})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            with _engine.connect() as conn:
                persona_id = None
                if persona_row:
                    pid_row = conn.execute(
                        text("SELECT id FROM personas WHERE user_id = :uid AND is_active = true ORDER BY created_at DESC LIMIT 1"),
                        {"uid": body.user_id}
                    ).fetchone()
                    if pid_row:
                        persona_id = str(pid_row[0])
                _save_message(conn, body.user_id, "user", body.message, persona_id)
                _save_message(conn, body.user_id, "assistant", full_response, persona_id)
                conn.commit()

            try:
                from routers.questions import _extract_persona_from_answer, _update_persona
                extracted = _extract_persona_from_answer(body.message, full_response)
                if extracted:
                    _update_persona(body.user_id, extracted)
            except Exception as e:
                print(f"[chat] Persona extraction warning: {e}")

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat/{message_id}/regenerate")
def regenerate(message_id: str, current_user: dict = Depends(get_current_user)):
    try:
        with _engine.connect() as conn:
            msg = conn.execute(
                text("SELECT user_id, content FROM messages WHERE id = :id AND role = 'assistant'"),
                {"id": message_id}
            ).fetchone()

            if not msg:
                raise HTTPException(status_code=404, detail="Message not found")

            user_id = msg[0]

            user_msg = conn.execute(
                text("""SELECT content FROM messages
                         WHERE user_id = :uid AND role = 'user'
                         AND created_at < (SELECT created_at FROM messages WHERE id = :id)
                         ORDER BY created_at DESC LIMIT 1"""),
                {"uid": user_id, "id": message_id}
            ).fetchone()

        if not user_msg:
            raise HTTPException(status_code=404, detail="Original user message not found")

        from services.ai.rag.retriever import search_hybrid
        from llm.router import chat_completion

        result = search_hybrid(user_id, user_msg[0], k=5)
        memory_block = "\n".join([f"- {c.text}" for c in result.chunks])

        messages = [
            {"role": "system", "content": "You are an AI twin of a real person. Respond in first person naturally."},
            {"role": "user", "content": f"Relevant memories:\n{memory_block}\n\nUser: {user_msg[0]}" if memory_block else user_msg[0]}
        ]

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
