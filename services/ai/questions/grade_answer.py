import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv(Path(__file__).resolve().parents[1] / "rag" / ".env")

# Configure Gemini
client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def grade_answer(question: str, answer: str) -> dict:
    """
    LLM judge that evaluates whether a user's answer is substantive.
    Catches non-answers like 'idk', 'skip', or off-topic responses.

    Args:
        question: The interview question that was asked
        answer: The user's response

    Returns:
        Dictionary with 'substantive' (bool) and 'reason' (str)
    """
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

    response = client_gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    # Parse JSON response
    import json
    text = response.text.strip()
    # Remove markdown code blocks if present
    text = text.replace("```json", "").replace("```", "").strip()
    result = json.loads(text)

    return {
        "substantive": result["substantive"],
        "reason": result["reason"]
    }

# Quick test
# if __name__ == "__main__":
#     tests = [
#         ("What do you do for work?", "I am a software engineer at a startup"),
#         ("What do you do for work?", "idk"),
#         ("What are your hobbies?", "skip"),
#         ("Where do you live?", "Lahore"),
#         ("What are your goals?", "I want to start my own company someday"),
#     ]
#
#     for question, answer in tests:
#         result = grade_answer(question, answer)
#         status = "✅" if result["substantive"] else "❌"
#         print(f"{status} Q: {question}")
#         print(f"   A: {answer}")
#         print(f"   Reason: {result['reason']}\n")