"""
services/api/voice/stt.py
=========================
Groq Whisper STT wrapper.
 
Usage:
    from voice.stt import transcribe
    result = await transcribe(audio_bytes, content_type="audio/webm")
    # result = {"text": "...", "duration_s": 4.2, "audio_id": "uuid"}
"""
from __future__ import annotations
 
import os
import uuid
 
from storage.client import upload_bytes, R2_AUDIO_BUCKET
 
# Groq client — singleton
_groq_client = None
 
 
def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable not set")
        _groq_client = Groq(api_key=api_key)
    return _groq_client
 
 
# Map content_type to file extension for Groq
CONTENT_TYPE_EXT = {
    "audio/webm":          "audio.webm",
    "audio/mp4":           "audio.mp4",
    "audio/wav":           "audio.wav",
    "audio/mpeg":          "audio.mp3",
    "audio/ogg":           "audio.ogg",
    "audio/flac":          "audio.flac",
    "video/webm":          "audio.webm",
    "audio/vnd.dlna.adts": "audio.m4a",
    "audio/aac":           "audio.m4a",
    "audio/x-m4a":         "audio.m4a",
}
 
# AAC content types that need to be sent as m4a to Groq
AAC_TYPES = {"audio/vnd.dlna.adts", "audio/aac", "audio/x-m4a"}
 
 
async def transcribe(audio_bytes: bytes, content_type: str) -> dict:
    """
    Transcribe audio using Groq Whisper.
 
    Steps:
        1. Generate unique audio_id
        2. Save raw audio to R2 immediately
        3. Call Groq Whisper API
        4. Return {text, duration_s, audio_id}
 
    Args:
        audio_bytes:  Raw audio file bytes
        content_type: MIME type (audio/webm, audio/wav, audio/mp4, etc.)
 
    Returns:
        {
            "text":       str,   # Transcribed text
            "duration_s": float, # Audio duration in seconds
            "audio_id":   str,   # UUID — use to reference this recording
        }
    """
    if not audio_bytes:
        raise ValueError("audio_bytes is empty")
 
    # Step 1 — Generate unique ID for this recording
    audio_id = str(uuid.uuid4())
 
    # Step 2 — Save raw audio to R2 immediately (before transcription)
    ext = CONTENT_TYPE_EXT.get(content_type, "audio.webm")
    r2_key = f"audio/{audio_id}/{ext}"
 
    upload_bytes(
        key=r2_key,
        data=audio_bytes,
        content_type=content_type,
        bucket=R2_AUDIO_BUCKET,
    )
    print(f"[stt] Saved audio to R2: {r2_key}")
 
    # Step 3 — Call Groq Whisper API
    client = _get_groq_client()
 
    # Force m4a filename and audio/mp4 MIME for AAC — Groq rejects .aac
    if content_type in AAC_TYPES:
        groq_filename = "audio.m4a"
        groq_mime = "audio/mp4"
    else:
        groq_filename = ext
        groq_mime = content_type
 
    transcription = client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=(groq_filename, audio_bytes, groq_mime),
        response_format="verbose_json",  # includes duration
    )
 
    text = transcription.text or ""
    duration_s = getattr(transcription, "duration", None)
 
    # Fallback duration estimate if not returned
    if duration_s is None:
        duration_s = round(len(audio_bytes) / 16000, 2)
 
    print(f"[stt] Transcribed {duration_s}s of audio: '{text[:60]}...'")
 
    return {
        "text":       text,
        "duration_s": round(float(duration_s), 2),
        "audio_id":   audio_id,
    }