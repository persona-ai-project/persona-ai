import os
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Circuit breaker state per provider
_circuit = {}
CIRCUIT_TRIP_DURATION = 60
CIRCUIT_ERROR_DURATION = 10


def _is_circuit_open(provider: str) -> bool:
    if provider not in _circuit:
        return False
    entry = _circuit[provider]
    duration = CIRCUIT_TRIP_DURATION if entry["type"] == "rate_limit" else CIRCUIT_ERROR_DURATION
    return (time.time() - entry["time"]) < duration


def _trip_circuit(provider: str, error_type: str = "error"):
    _circuit[provider] = {"time": time.time(), "type": error_type}


def _try_groq(messages: list, model: str = "llama-3.1-8b-instant") -> str:
    if _is_circuit_open("groq"):
        raise RuntimeError("Groq circuit open")
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model, messages=messages, max_tokens=1024, temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        error_type = "rate_limit" if "429" in str(e) or "rate" in str(e).lower() else "error"
        _trip_circuit("groq", error_type)
        raise


def _try_cerebras(messages: list) -> str:
    if _is_circuit_open("cerebras"):
        raise RuntimeError("Cerebras circuit open")
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        raise RuntimeError("No CEREBRAS_API_KEY")
    try:
        import httpx
        resp = httpx.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "llama-3.1-8b", "messages": messages, "max_tokens": 1024, "temperature": 0.7},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        error_type = "rate_limit" if "429" in str(e) or "rate" in str(e).lower() else "error"
        _trip_circuit("cerebras", error_type)
        raise


def _try_gemini(messages: list) -> str:
    if _is_circuit_open("gemini"):
        raise RuntimeError("Gemini circuit open")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("No GEMINI_API_KEY")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model_instance = genai.GenerativeModel("gemini-2.0-flash")
        prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
        response = model_instance.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        error_type = "rate_limit" if "429" in str(e) or "rate" in str(e).lower() else "error"
        _trip_circuit("gemini", error_type)
        raise


def chat_completion(messages: list, model: str = "llama-3.1-8b-instant", max_tokens: int = 1024) -> str:
    providers = [
        ("groq", lambda: _try_groq(messages, model)),
        ("cerebras", lambda: _try_cerebras(messages)),
        ("gemini", lambda: _try_gemini(messages)),
    ]

    last_error = None
    for name, fn in providers:
        try:
            result = fn()
            print(f"[LLMRouter] {name} succeeded")
            return result
        except Exception as e:
            print(f"[LLMRouter] {name} failed: {e}")
            last_error = e

    raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")
