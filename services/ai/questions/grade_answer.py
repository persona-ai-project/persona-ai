import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / "rag" / ".env")

NON_SUBSTANTIVE = re.compile(
    r"^(idk|i don'?t know|skip|nothing|nah|no|n/a|none|ok|okay|whatever|idc|lol|haha|yes|no|sure|maybe|yep|nope|fine|good|bad|cool|nice|great|ok|same)\s*[!.]?\s*$",
    re.IGNORECASE,
)


def _simple_grade(question: str, answer: str) -> dict:
    """Fallback grading when no LLM is available."""
    clean = answer.strip().lower()
    if len(clean) < 2 or NON_SUBSTANTIVE.match(clean):
        return {"substantive": False, "reason": "Answer too short or non-substantive"}
    if len(clean.split()) < 2 and not any(c.isdigit() for c in clean):
        return {"substantive": False, "reason": "Single word answer, needs more detail"}
    return {"substantive": True, "reason": "Answer contains useful information"}


def grade_answer(question: str, answer: str) -> dict:
    """
    LLM judge that evaluates whether a user's answer is substantive.
    Falls back to simple keyword-based grading if no LLM is available.
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return _simple_grade(question, answer)

        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""
        You are evaluating whether a user's answer to an interview question is useful.

        Question: {question}
        Answer: {answer}

        Is this answer substantive and useful for building a personal profile?

        Rules:
        - "idk", "skip", "nothing", "I don't know", "n/a" = NOT substantive
        - Very short answers under 2 words = NOT substantive
        - Single proper nouns as location answers ARE substantive (e.g. "Lahore", "London")
        - Off-topic answers = NOT substantive
        - Any real, genuine answer = substantive

        Respond in this exact JSON format:
        {{"substantive": true/false, "reason": "one sentence explanation"}}

        Return ONLY the JSON, nothing else.
        """

        response = model.generate_content(prompt)

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)

        return {
            "substantive": result["substantive"],
            "reason": result["reason"]
        }
    except Exception as e:
        print(f"[grade_answer] LLM fallback triggered: {e}")
        return _simple_grade(question, answer)
