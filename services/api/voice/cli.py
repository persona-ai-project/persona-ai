
"""
services/api/voice/cli.py
=========================
CLI tool for offline voice testing.
 
Usage:
    python -m voice transcribe path/to/audio.wav
    python -m voice synthesise "hello world" --voice en_US-lessac-medium
    python -m voice voices
"""
from __future__ import annotations
 
import sys
import os
import time
import argparse
import asyncio
from pathlib import Path
 
# Add parent to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
 
def cmd_transcribe(args):
    """Transcribe an audio file and print the result."""
    audio_path = Path(args.file)
    if not audio_path.exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)
 
    ext_map = {
        ".wav":  "audio/wav",
        ".mp3":  "audio/mpeg",
        ".mp4":  "audio/mp4",
        ".webm": "audio/webm",
        ".ogg":  "audio/ogg",
        ".flac": "audio/flac",
        ".m4a":  "audio/x-m4a",
        ".aac":  "audio/aac",
    }
    ext = audio_path.suffix.lower()
    content_type = ext_map.get(ext, "audio/wav")
 
    print(f"Transcribing: {audio_path} ({content_type})")
    print(f"File size: {audio_path.stat().st_size / 1024:.1f} KB")
 
    audio_bytes = audio_path.read_bytes()
 
    from voice.stt import transcribe
 
    start = time.perf_counter()
    result = asyncio.run(transcribe(audio_bytes, content_type))
    latency_ms = int((time.perf_counter() - start) * 1000)
 
    print(f"\n{'='*50}")
    print(f"Text:       {result['text']}")
    print(f"Duration:   {result['duration_s']}s")
    print(f"Audio ID:   {result['audio_id']}")
    print(f"Latency:    {latency_ms}ms")
    print(f"{'='*50}")
 
    if latency_ms <= 1500:
        print(f"✅ Under 1500ms target")
    else:
        print(f"⚠️  Over 1500ms target ({latency_ms}ms)")
 
 
def cmd_synthesise(args):
    """Synthesise speech from text and save to file."""
    from voice.tts import synthesise, list_voices
 
    available = list_voices()
    if args.voice not in available:
        print(f"Error: Voice '{args.voice}' not found.")
        print(f"Available: {available}")
        sys.exit(1)
 
    print(f"Synthesising: '{args.text[:50]}...'" if len(args.text) > 50 else f"Synthesising: '{args.text}'")
    print(f"Voice: {args.voice}")
 
    start = time.perf_counter()
    url = asyncio.run(synthesise(args.text, args.voice))
    latency_ms = int((time.perf_counter() - start) * 1000)
 
    print(f"\n{'='*50}")
    print(f"URL:      {url[:80]}...")
    print(f"Latency:  {latency_ms}ms")
    print(f"Cached:   {'Yes ✅' if latency_ms < 100 else 'No'}")
    print(f"{'='*50}")
 
 
def cmd_voices(args):
    """List available voice models."""
    from voice.tts import list_voices
    voices = list_voices()
    print(f"Available voices ({len(voices)}):")
    for v in voices:
        marker = " (default)" if v == "en_US-lessac-medium" else ""
        print(f"  - {v}{marker}")
 
 
def main():
    parser = argparse.ArgumentParser(
        prog="voice",
        description="Persona AI Voice CLI — test STT and TTS offline"
    )
    subparsers = parser.add_subparsers(dest="command")
 
    p_transcribe = subparsers.add_parser("transcribe", help="Transcribe an audio file")
    p_transcribe.add_argument("file", help="Path to audio file (.wav, .mp3, .m4a, etc.)")
 
    p_synthesise = subparsers.add_parser("synthesise", help="Synthesise speech from text")
    p_synthesise.add_argument("text", help="Text to synthesise")
    p_synthesise.add_argument(
        "--voice",
        default="en_US-lessac-medium",
        help="Voice model ID (default: en_US-lessac-medium)"
    )
 
    subparsers.add_parser("voices", help="List available voice models")
 
    args = parser.parse_args()
 
    if args.command == "transcribe":
        cmd_transcribe(args)
    elif args.command == "synthesise":
        cmd_synthesise(args)
    elif args.command == "voices":
        cmd_voices(args)
    else:
        parser.print_help()
 
 
if __name__ == "__main__":
    main()