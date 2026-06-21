import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Load env
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def chat_completion(messages: list, model: str = "llama-3.1-8b-instant") -> str:
    """
    Send messages to Groq LLM.
    Falls back to Gemini if Groq fails.

    Args:
        messages: List of {role, content} dicts
        model: Groq model to use

    Returns:
        Assistant response text
    """
    try:
        # Try Groq first
        response = groq_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
        )
        return response.choices[0].message.content

    except Exception as groq_error:
        print(f"[LLMRouter] Groq failed: {groq_error} — falling back to Gemini")

        # Fallback to Gemini
        try:
            from google import genai
            from services.ai.rag.embedder import load_dotenv as _
            gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            # Convert messages to single prompt
            prompt = "\n".join([
                f"{m['role'].upper()}: {m['content']}"
                for m in messages
            ])

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()

        except Exception as gemini_error:
            print(f"[LLMRouter] Gemini also failed: {gemini_error}")
            raise RuntimeError("All LLM providers failed")