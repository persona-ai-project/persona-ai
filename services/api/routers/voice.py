from __future__ import annotations

import time
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/voice", tags=["voice"])

ALLOWED_CONTENT_TYPES = {
    "audio/webm",
    "audio/mp4",
    "audio/wav",
    "audio/mpeg",
    "audio/ogg",
    "audio/flac",
    "video/webm",
    "audio/vnd.dlna.adts",
    "audio/aac",
    "audio/x-m4a",
}

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
):
    """
    Transcribe audio using Groq Whisper.
    Accepts: audio/webm, audio/mp4, audio/wav, audio/mpeg, audio/ogg, audio/flac
    """
    content_type = file.content_type or "audio/webm"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {content_type}."
        )

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(audio_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(audio_bytes)/1024/1024:.1f}MB. Max: 25MB"
        )

    start = time.perf_counter()
    try:
        from voice.stt import transcribe
        result = await transcribe(audio_bytes, content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Transcription failed")

    latency_ms = int((time.perf_counter() - start) * 1000)
    return {**result, "latency_ms": latency_ms}


@router.get("/voices")
def get_voices():
    """List all available TTS voice models."""
    try:
        from voice.tts import list_voices
        voices = list_voices()
    except Exception:
        voices = ["en_US-lessac-medium"]
    return {
        "voices": voices,
        "default": "en_US-lessac-medium",
        "total": len(voices),
    }


@router.post("/synthesise")
async def synthesise_speech(
    text: str,
    voice_id: str = "en_US-lessac-medium",
):
    """Synthesise speech from text using Piper TTS."""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    if len(text) > 5000:
        raise HTTPException(status_code=400, detail=f"Text too long. Max: 5000")

    start = time.perf_counter()
    try:
        from voice.tts import synthesise
        url = await synthesise(text, voice_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

    latency_ms = int((time.perf_counter() - start) * 1000)
    return {
        "url": url,
        "voice_id": voice_id,
        "char_count": len(text),
        "latency_ms": latency_ms,
        "cached": latency_ms < 100,
    }