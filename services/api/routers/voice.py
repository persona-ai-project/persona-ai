"""
routers/voice.py
================
Voice transcription HTTP routes.

Routes:
    POST /voice/transcribe — upload audio, get back text
"""
from __future__ import annotations

import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from voice.stt import transcribe

router = APIRouter(prefix="/voice", tags=["voice"])

ALLOWED_CONTENT_TYPES = {
    "audio/webm",
    "audio/mp4",
    "audio/wav",
    "audio/mpeg",
    "audio/ogg",
    "audio/flac",
    "video/webm",   # MediaRecorder sometimes sends this
    "audio/vnd.dlna.adts",   # AAC — iPhone voice memos
    "audio/aac",              # AAC variant
    "audio/x-m4a",           # M4A — iPhone voice memos
}

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB — Groq's limit


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
):
    """
    Transcribe audio using Groq Whisper.

    Accepts: audio/webm, audio/mp4, audio/wav, audio/mpeg, audio/ogg, audio/flac

    Returns:
        {
            "text":       str,    # Transcribed text
            "duration_s": float,  # Audio duration in seconds
            "audio_id":   str,    # UUID for this recording (stored in R2)
            "latency_ms": int,    # Total transcription time in ms
        }
    """
    # Validate content type
    content_type = file.content_type or "audio/webm"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {content_type}. "
                   f"Allowed: {sorted(ALLOWED_CONTENT_TYPES)}"
        )

    # Read file bytes
    audio_bytes = await file.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(audio_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(audio_bytes) / 1024 / 1024:.1f}MB. Max: 25MB"
        )

    # Transcribe
    start = time.perf_counter()
    try:
        result = await transcribe(audio_bytes, content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"[voice] Transcription error: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")

    latency_ms = int((time.perf_counter() - start) * 1000)
    print(f"[voice] Total latency: {latency_ms}ms")

    return {
        **result,
        "latency_ms": latency_ms,
    }