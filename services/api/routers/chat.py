import os
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from core.security import get_current_user

# Load env
load_dotenv(Path(__file__).resolve().parents[2] / "ai" / "rag" / ".env")

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    chunks_used: list[str]


@router.post("", response_model=ChatResponse)
def chat(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Chat with the AI twin.
    Retrieves relevant memories via RAG and generates a response.
    Requires JWT token in Authorization header.
    """
    try:
        from services.ai.rag.retriever import search_hybrid
        from llm.router import chat_completion

        # Get relevant memories
        result = search_hybrid(body.user_id, body.message, k=5)

        # Build memory block
        memory_block = "\n".join([
            f"- {chunk.text}"
            for chunk in result.chunks
        ])

        # Build prompt
        prompt = f"""You are an AI twin of a real person.

Here are relevant memories about this person:
{memory_block}

Respond to this message as that person would — in first person, naturally:
User: {body.message}
"""

        messages = [
            {"role": "system", "content": "You are an AI twin of a real person. Respond in first person naturally."},
            {"role": "user", "content": prompt}
        ]

        reply = chat_completion(messages)

        return ChatResponse(
            reply=reply,
            chunks_used=[chunk.text for chunk in result.chunks]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Stream chat response token by token — like ChatGPT!
    Requires JWT token in Authorization header.
    """
    from services.ai.rag.retriever import search_hybrid

    # Get RAG chunks
    result = search_hybrid(body.user_id, body.message, k=5)
    memory_block = "\n".join([f"- {chunk.text}" for chunk in result.chunks])

    prompt = f"""You are an AI twin of a real person.
Here are relevant memories:
{memory_block}

Respond naturally in first person:
User: {body.message}"""

    async def generate():
        try:
            from groq import Groq
            load_dotenv(Path(__file__).resolve().parents[1] / ".env")

            client = Groq(api_key=os.getenv("GROQ_API_KEY"))

            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an AI twin. Respond in first person naturally."},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
                max_tokens=500
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'token': token})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")