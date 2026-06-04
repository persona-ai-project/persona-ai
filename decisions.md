# Architecture Decisions

## ADR-001: Voice Contract v1.0
**Date:** Day 13
**Status:** Frozen
**Decided by:** P2 + P3 sync

### Context
P3 needs to wire VoiceRecorder component to POST /voice/transcribe.
Contract must be frozen before P3 starts UI work.

### Decision
TranscribeResponse contract frozen as:
```json
{
  "text": "string",
  "duration_s": 0.0,
  "audio_id": "uuid-string",
  "latency_ms": 0
}
```

### What P3 confirmed they DON'T need (for now):
- Confidence score (Groq doesn't return one; add in v2 if needed)
- Word-level timestamps (no current UI use case)
- Playback URL (audio_id is sufficient; P3 will construct URL if needed)

### Consequences
- No new fields without new ADR entry + P2 review
- If P3 needs confidence score later → ADR-002