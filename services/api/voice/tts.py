"""
services/api/voice/tts.py
=========================
Piper TTS wrapper with SHA256 cache.
 
Usage:
    from voice.tts import synthesise, list_voices
    url = await synthesise("Hello world", "en_US-lessac-medium")
    voices = list_voices()
"""
from __future__ import annotations
 
import os
import io
import wave
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
 
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
 
from storage.client import upload_bytes, get_presigned_url, R2_AUDIO_BUCKET
 
# ── paths ─────────────────────────────────────────────────────────────────────
 
VOICES_DIR = Path(__file__).parent / "voices"
DEFAULT_VOICE = "en_US-lessac-medium"
 
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)
 
# ── voice model singleton cache ───────────────────────────────────────────────
 
_loaded_voices: dict = {}
 
 
def _get_voice(voice_id: str):
    """Load and cache Piper voice model (singleton per voice_id)."""
    if voice_id not in _loaded_voices:
        from piper import PiperVoice
        onnx_path = VOICES_DIR / f"{voice_id}.onnx"
        if not onnx_path.exists():
            raise ValueError(
                f"Voice model not found: {voice_id}. "
                f"Available: {list_voices()}"
            )
        print(f"[tts] Loading voice model: {voice_id}")
        _loaded_voices[voice_id] = PiperVoice.load(str(onnx_path))
        print(f"[tts] Voice model loaded: {voice_id}")
    return _loaded_voices[voice_id]
 
 
# ── cache helpers ─────────────────────────────────────────────────────────────
 
def _cache_key(text: str, voice_id: str) -> str:
    """SHA256 hash of text + voice_id."""
    return hashlib.sha256(f"{text}:{voice_id}".encode()).hexdigest()
 
 
def _cache_get(text_hash: str) -> Optional[str]:
    """Look up cache by text_hash. Returns audio_url if hit, None if miss."""
    try:
        engine = create_engine(DATABASE_URL)
        db = sessionmaker(bind=engine)()
        result = db.execute(
            text("SELECT audio_url FROM voice_cache WHERE text_hash = :hash"),
            {"hash": text_hash}
        ).fetchone()
        db.close()
        if result:
            print(f"[tts] Cache HIT: {text_hash[:16]}...")
            return result[0]
        print(f"[tts] Cache MISS: {text_hash[:16]}...")
        return None
    except Exception as e:
        print(f"[tts] Cache lookup error: {e}")
        return None
 
 
def _cache_set(
    text_hash: str,
    audio_url: str,
    voice_id: str,
    char_count: int,
    user_id: str = "c1b86221-ff7a-439b-bc6f-11a59bf50175",  # demo user
) -> None:
    """Insert cache row into voice_cache table."""
    try:
        engine = create_engine(DATABASE_URL)
        db = sessionmaker(bind=engine)()
        db.execute(
            text("""
                INSERT INTO voice_cache (id, user_id, text_hash, audio_url, created_at)
                VALUES (gen_random_uuid(), CAST(:user_id AS uuid), :hash, :url, :created_at)
                ON CONFLICT DO NOTHING
            """),
            {
                "user_id":    user_id,
                "hash":       text_hash,
                "url":        audio_url,
                "created_at": datetime.now(timezone.utc),
            }
        )
        db.commit()
        db.close()
        print(f"[tts] Cached: {text_hash[:16]}...")
    except Exception as e:
        print(f"[tts] Cache write error: {e}")
 
 
# ── public API ────────────────────────────────────────────────────────────────
 
def list_voices() -> list[str]:
    """Return list of available voice_ids from voices/ directory."""
    if not VOICES_DIR.exists():
        return []
    return sorted([
        f.stem
        for f in VOICES_DIR.glob("*.onnx")
        if not f.name.endswith(".json")
    ])
 
 
async def synthesise(text_input: str, voice_id: str = DEFAULT_VOICE) -> str:
    """
    Synthesise speech from text using Piper TTS.
 
    Cache logic:
        - Compute SHA256(text:voice_id)
        - Check voice_cache table
        - HIT:  return audio_url immediately (< 50ms)
        - MISS: synthesise → upload to R2 → cache → return URL
 
    Args:
        text_input: Text to synthesise (max 5000 chars recommended)
        voice_id:   Voice model ID (e.g. "en_US-lessac-medium")
 
    Returns:
        Presigned R2 URL to the generated WAV file (valid 1 hour)
    """
    if not text_input or not text_input.strip():
        raise ValueError("text_input is empty")
 
    # Step 1 — check cache
    key = _cache_key(text_input, voice_id)
    cached_url = _cache_get(key)
    if cached_url:
        try:
            r2_key = f"tts/{key[:16]}/{voice_id}.wav"
            return get_presigned_url(
                key=r2_key,
                bucket=R2_AUDIO_BUCKET,
                expires_in=3600,
                method="get_object"
            )
        except Exception:
            return cached_url
 
    # Step 2 — synthesise with Piper
    # synthesize() returns Iterable[AudioChunk], each has .audio_int16_bytes
    voice_model = _get_voice(voice_id)
 
    pcm_data = b""
    for chunk in voice_model.synthesize(text_input):
        pcm_data += chunk.audio_int16_bytes
 
    if not pcm_data:
        raise RuntimeError("Piper returned empty audio")
 
    # Wrap raw PCM in a proper WAV container
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)   # 16-bit
        wav_file.setframerate(voice_model.config.sample_rate)
        wav_file.writeframes(pcm_data)
 
    audio_bytes = buf.getvalue()
    print(f"[tts] Synthesised {len(pcm_data)} PCM bytes → {len(audio_bytes)} WAV bytes")
 
    # Step 3 — upload to R2
    r2_key = f"tts/{key[:16]}/{voice_id}.wav"
    upload_bytes(
        key=r2_key,
        data=audio_bytes,
        content_type="audio/wav",
        bucket=R2_AUDIO_BUCKET,
    )
    print(f"[tts] Uploaded to R2: {r2_key} ({len(audio_bytes)} bytes)")
 
    # Step 4 — get presigned URL
    storage_url = get_presigned_url(
        key=r2_key,
        bucket=R2_AUDIO_BUCKET,
        expires_in=3600,
        method="get_object"
    )
 
    # Step 5 — cache the result
    _cache_set(key, storage_url, voice_id, len(text_input))
 
    return storage_url
 