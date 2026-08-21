"""
routers/twin_voice.py
====================
Twin-aware voice chat endpoints.

Routes:
    POST /twins/{twin_id}/voice/chat         — voice chat (audio in, audio out)
    POST /twins/{twin_id}/voice/transcribe   — transcribe audio for twin
    POST /twins/{twin_id}/voice/synthesise   — synthesise speech for twin
    GET  /twins/{twin_id}/voice/config       — get voice configuration
    PATCH /twins/{twin_id}/voice/config      — update voice configuration
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from core.security import get_current_user

router = APIRouter(prefix="/twins", tags=["twin-voice"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)


# ── Models ──────────────────────────────────────────────────────────────────────

class VoiceConfigRequest(BaseModel):
    voice_id: str | None = None
    voice_enabled: bool | None = None
    voice_speed: float | None = None
    voice_pitch: float | None = None


class VoiceConfigResponse(BaseModel):
    voice_id: str
    voice_enabled: bool
    voice_speed: float
    voice_pitch: float
    languages: list[str]


class VoiceChatResponse(BaseModel):
    text_response: str
    audio_url: str | None = None
    transcription: str | None = None
    voice_id: str
    latency_ms: int


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _get_db():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _verify_twin_owner(conn, twin_id: str, user_id: str):
    """Verify user owns the twin."""
    row = conn.execute(
        text("""SELECT id, owner_id, voice_id, voice_enabled, voice_speed, voice_pitch, languages
                FROM twins WHERE id = :id AND is_active = true"""),
        {"id": twin_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Twin not found")
    if str(row[1]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return {
        "id": str(row[0]),
        "owner_id": str(row[1]),
        "voice_id": row[2] or "en_US-lessac-medium",
        "voice_enabled": row[3] if row[3] is not None else True,
        "voice_speed": row[4] if row[4] is not None else 1.0,
        "voice_pitch": row[5] if row[5] is not None else 1.0,
        "languages": row[6] or ["en"],
    }


def _get_twin_for_chat(conn, twin_id: str):
    """Get twin config for public/private chat."""
    row = conn.execute(
        text("""SELECT id, name, status, voice_id, voice_enabled, voice_speed, voice_pitch, languages,
                       default_language, personality_config
                FROM twins WHERE id = :id AND is_active = true"""),
        {"id": twin_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Twin not found")
    if row[2] != "active":
        raise HTTPException(status_code=403, detail="Twin is not active")
    return {
        "id": str(row[0]),
        "name": row[1],
        "status": row[2],
        "voice_id": row[3] or "en_US-lessac-medium",
        "voice_enabled": row[4] if row[4] is not None else True,
        "voice_speed": row[5] if row[5] is not None else 1.0,
        "voice_pitch": row[6] if row[6] is not None else 1.0,
        "languages": row[7] or ["en"],
        "default_language": row[8] or "en",
        "personality_config": row[9],
    }


def _select_voice_for_language(language: str, available_voices: list[str]) -> str:
    """Select appropriate voice for detected language."""
    # Map language codes to voice prefixes
    lang_voice_map = {
        "en": "en_US",
        "es": "es_ES",
        "fr": "fr_FR",
        "de": "de_DE",
        "it": "it_IT",
        "pt": "pt_BR",
        "ru": "ru_RU",
        "nl": "nl_NL",
        "pl": "pl_PL",
        "sv": "sv_SE",
        "da": "da_DK",
        "no": "nb_NO",
        "fi": "fi_FI",
        "tr": "tr_TR",
        "ar": "ar_SA",
        "hi": "hi_IN",
        "ja": "ja_JP",
        "zh": "zh_CN",
        "ko": "ko_KR",
    }
    
    prefix = lang_voice_map.get(language, "en_US")
    
    # Find matching voice
    for voice in available_voices:
        if voice.startswith(prefix):
            return voice
    
    # Fallback to default
    return "en_US-lessac-medium"


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.get("/{twin_id}/voice/config", response_model=VoiceConfigResponse)
def get_voice_config(
    twin_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get voice configuration for a twin."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        twin = _verify_twin_owner(db, twin_id, user_id)
        return VoiceConfigResponse(
            voice_id=twin["voice_id"],
            voice_enabled=twin["voice_enabled"],
            voice_speed=twin["voice_speed"],
            voice_pitch=twin["voice_pitch"],
            languages=twin["languages"],
        )
    finally:
        db.close()


@router.patch("/{twin_id}/voice/config", response_model=VoiceConfigResponse)
def update_voice_config(
    twin_id: str,
    body: VoiceConfigRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update voice configuration for a twin."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        twin = _verify_twin_owner(db, twin_id, user_id)

        # Build update
        updates = []
        params = {"id": twin_id}

        if body.voice_id is not None:
            updates.append("voice_id = :voice_id")
            params["voice_id"] = body.voice_id

        if body.voice_enabled is not None:
            updates.append("voice_enabled = :voice_enabled")
            params["voice_enabled"] = body.voice_enabled

        if body.voice_speed is not None:
            if not 0.5 <= body.voice_speed <= 2.0:
                raise HTTPException(status_code=400, detail="Voice speed must be between 0.5 and 2.0")
            updates.append("voice_speed = :voice_speed")
            params["voice_speed"] = body.voice_speed

        if body.voice_pitch is not None:
            if not 0.5 <= body.voice_pitch <= 2.0:
                raise HTTPException(status_code=400, detail="Voice pitch must be between 0.5 and 2.0")
            updates.append("voice_pitch = :voice_pitch")
            params["voice_pitch"] = body.voice_pitch

        if updates:
            updates.append("updated_at = :now")
            params["now"] = datetime.now(timezone.utc)

            db.execute(
                text(f"UPDATE twins SET {', '.join(updates)} WHERE id = :id"),
                params
            )
            db.commit()

        # Re-fetch
        twin = _verify_twin_owner(db, twin_id, user_id)
        return VoiceConfigResponse(
            voice_id=twin["voice_id"],
            voice_enabled=twin["voice_enabled"],
            voice_speed=twin["voice_speed"],
            voice_pitch=twin["voice_pitch"],
            languages=twin["languages"],
        )
    finally:
        db.close()


@router.post("/{twin_id}/voice/transcribe")
async def transcribe_for_twin(
    twin_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Transcribe audio for a specific twin."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        twin = _verify_twin_owner(db, twin_id, user_id)
    finally:
        db.close()

    if not twin["voice_enabled"]:
        raise HTTPException(status_code=400, detail="Voice is disabled for this twin")

    # Transcribe
    content_type = file.content_type or "audio/webm"
    audio_bytes = await file.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        from voice.stt import transcribe
        result = await transcribe(audio_bytes, content_type)
        return {
            **result,
            "twin_id": twin_id,
            "voice_id": twin["voice_id"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/{twin_id}/voice/synthesise")
async def synthesise_for_twin(
    twin_id: str,
    text: str,
    voice_id: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    """Synthesise speech for a specific twin."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        twin = _verify_twin_owner(db, twin_id, user_id)
    finally:
        db.close()

    if not twin["voice_enabled"]:
        raise HTTPException(status_code=400, detail="Voice is disabled for this twin")

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    # Use twin's voice or specified voice
    use_voice = voice_id or twin["voice_id"]

    try:
        from voice.tts import synthesise
        url = await synthesise(text, use_voice)
        return {
            "url": url,
            "voice_id": use_voice,
            "twin_id": twin_id,
            "speed": twin["voice_speed"],
            "pitch": twin["voice_pitch"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.post("/{twin_id}/voice/chat", response_model=VoiceChatResponse)
async def voice_chat(
    twin_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Voice chat with a twin: audio in → text response → audio out.
    """
    import time
    start_time = time.perf_counter()
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        twin = _get_twin_for_chat(db, twin_id)
    finally:
        db.close()

    if not twin["voice_enabled"]:
        raise HTTPException(status_code=400, detail="Voice is disabled for this twin")

    # 1. Transcribe audio
    content_type = file.content_type or "audio/webm"
    audio_bytes = await file.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        from voice.stt import transcribe
        stt_result = await transcribe(audio_bytes, content_type)
        user_text = stt_result.get("text", "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    if not user_text.strip():
        raise HTTPException(status_code=400, detail="No speech detected")

    # 2. Generate text response using twin chat logic
    try:
        from services.ai.language.detector import detect_language
        from services.ai.rag.retriever import search_hybrid

        # Detect language
        detected_lang = detect_language(user_text)
        user_language = detected_lang["code"] if detected_lang["confidence"] >= 0.5 else None

        # Load knowledge
        knowledge_chunks = []
        try:
            result = search_hybrid(twin["id"], user_text, k=5, twin_id=twin_id)
            for chunk in result.chunks:
                knowledge_chunks.append({
                    "text": chunk.text,
                    "score": round(float(getattr(chunk, 'score', 0) or 0), 3),
                })
        except Exception as e:
            print(f"[twin_voice] Knowledge retrieval warning: {e}")

        # Build prompt
        from routers.twin_chat import _build_system_prompt
        system_prompt = _build_system_prompt(
            twin,
            knowledge_chunks,
            [],
            user_language,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]

        from llm.router import chat_completion
        text_response = chat_completion(messages, max_tokens=512)

    except Exception as e:
        text_response = f"I'm sorry, I couldn't process that. Could you try again?"

    # 3. Synthesise speech
    audio_url = None
    try:
        from voice.tts import synthesise
        # Select voice based on detected language
        from voice.tts import list_voices
        available_voices = list_voices()
        voice_for_lang = _select_voice_for_language(
            user_language or twin["default_language"],
            available_voices
        )
        use_voice = twin["voice_id"] if twin["voice_id"] != "en_US-lessac-medium" else voice_for_lang

        audio_url = await synthesise(text_response, use_voice)
    except Exception as e:
        print(f"[twin_voice] TTS warning: {e}")

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    return VoiceChatResponse(
        text_response=text_response,
        audio_url=audio_url,
        transcription=user_text,
        voice_id=twin["voice_id"],
        latency_ms=latency_ms,
    )


from sqlalchemy.orm import sessionmaker
