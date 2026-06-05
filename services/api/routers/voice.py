"""
routers/voice.py
================
Voice routes: STT transcription + TTS synthesis.
"""
from __future__ import annotations
 
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from shared.contracts.voice import TranscribeResponse, SynthesiseResponse, VoicesResponse
 
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
 
 
@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
):
    """
    Transcribe audio using Groq Whisper.
    Accepts: audio/webm, audio/mp4, audio/wav, audio/mpeg, audio/ogg, audio/flac
    """
    from voice.stt import transcribe
 
    content_type = file.content_type or "audio/webm"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {content_type}. "
                   f"Allowed: {sorted(ALLOWED_CONTENT_TYPES)}"
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
 
    return {**result, "latency_ms": latency_ms}
 
 
@router.get("/voices", response_model=VoicesResponse)
def get_voices():
    """
    List all available TTS voice models.
    Returns list of voice_id strings ready to use in POST /voice/synthesise.
    """
    from voice.tts import list_voices
    voices = list_voices()
    return {
        "voices": voices,
        "default": "en_US-lessac-medium",
        "total": len(voices),
    }
 
 
@router.post("/synthesise", response_model=SynthesiseResponse)
async def synthesise_speech(
    text: str,
    voice_id: str = "en_US-lessac-medium",
):
    """
    Synthesise speech from text using Piper TTS.
 
    Cache: SHA256(text:voice_id) — cache hits return in < 50ms.
    First synthesis of 100-char text: < 1 second on CPU.
 
    Returns presigned R2 URL to WAV file (valid 1 hour).
    """
    from voice.tts import synthesise
 
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="text is required")
 
    if len(text) > 5000:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long: {len(text)} chars. Max: 5000"
        )
 
    start = time.perf_counter()
    try:
        url = await synthesise(text, voice_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[voice] TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
 
    latency_ms = int((time.perf_counter() - start) * 1000)
    print(f"[voice] TTS latency: {latency_ms}ms")
 
    return {
        "url":        url,
        "voice_id":   voice_id,
        "char_count": len(text),
        "latency_ms": latency_ms,
        "cached":     latency_ms < 100,
    }