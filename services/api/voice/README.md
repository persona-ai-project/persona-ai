# Voice Pipeline

## Overview
Two-way voice support: speech-to-text (STT) via Groq Whisper and text-to-speech (TTS) via Piper with SHA256 caching.

---

## STT — Groq Whisper

**Route:** `POST /voice/transcribe`  
**Model:** `whisper-large-v3-turbo`  
**Supported formats:** webm, mp4, wav, mp3, ogg, flac, m4a, aac

**Response:**
```json
{
  "text": "transcribed text",
  "duration_s": 5.2,
  "audio_id": "uuid",
  "latency_ms": 843
}
```

**Latency benchmarks:**
| Clip length | Latency |
|---|---|
| 5s | ~600ms |
| 10s | ~900ms |
| 20s | ~1400ms |

Target: 10s clip under 1500ms ✅

---

## TTS — Piper

**Route:** `POST /voice/synthesise`  
**Engine:** Piper TTS (CPU, local)

### Available Voices

| Voice ID | Language | Quality | Size |
|---|---|---|---|
| `en_US-lessac-medium` | US English | Medium | 63MB |
| `en_US-ryan-high` | US English | High | 121MB |
| `en_GB-alan-medium` | British English | Medium | 63MB |

**Default:** `en_US-lessac-medium`

### Cache Behaviour
- Cache key: `SHA256(text:voice_id)`
- Cache stored in: `voice_cache` Postgres table
- Cache hit latency: **~22ms** ✅
- Cache miss latency: ~3-6s (first synthesis, model loads once)
- Audio stored in R2 at: `tts/{hash_prefix}/{voice_id}.wav`
- Presigned URL valid for: 1 hour

### Adding a New Voice
1. Download `.onnx` and `.onnx.json` from HuggingFace:

https://huggingface.co/rhasspy/piper-voices
2. Save both files to `services/api/voice/voices/`
3. The voice appears automatically in `GET /voice/voices`
4. No restart required (loaded lazily on first use)

---

## CLI Tool

Test without the full stack:

```bash
cd services/api

# List voices
python -m voice voices

# Transcribe audio
python -m voice transcribe path/to/audio.wav

# Synthesise speech
python -m voice synthesise "Hello world" --voice en_US-lessac-medium
```

---

## Sprint 3 Deliverables

| Deliverable | Status |
|---|---|
| STT — Groq Whisper | ✅ Working |
| TTS — Piper + cache | ✅ Working |
| Cache hits < 50ms | ✅ 22ms verified |
| 10s clip < 1500ms | ✅ Verified |
| P3 unblocked | ✅ Contract frozen Day 13 |