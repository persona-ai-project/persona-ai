import os
import json
from dotenv import load_dotenv
from google import genai
from services.ai.questions.assess_gaps import assess_gaps

# Load environment variables
from pathlib import Path
env_path = Path(__file__).resolve().parents[1] / "rag" / ".env"
load_dotenv(env_path)

# Configure Gemini
client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def next_question(user_id: str, persona_json: dict) -> dict:
    """
    Generate the next interview question based on persona gaps.

    Args:
        user_id: Unique identifier for the user
        persona_json: Current state of user's persona

    Returns:
        NextQuestionResponse with question, gap_field, gap_type
    """
    # Find gaps in persona
    gaps = assess_gaps(persona_json)

    # If no gaps found, persona is complete
    if not gaps:
        return {
            "user_id": user_id,
            "question": "Tell me something interesting about yourself that I might not know!",
            "gap_field": "general",
            "gap_type": "none"
        }

    # Pick the most important gap (first one)
    top_gap = gaps[0]

    # Build prompt for Gemini
    prompt = f"""
    You are a friendly interviewer building a personal AI twin for someone.

    The user's current persona is:
    {json.dumps(persona_json, indent=2)}

    There is a gap in their profile:
    - Field: {top_gap['field']}
    - Gap type: {top_gap['gap_type']}
    - Reason: {top_gap['reason']}

    Generate ONE natural, conversational question to fill this gap.

    Rules:
    - Maximum 20 words
    - Friendly and casual tone
    - Do not mention "AI twin" or "profile"
    - Return ONLY the question, nothing else
    """

    # Call Gemini API
    response = client_gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    question = response.text.strip()

    return {
        "user_id": user_id,
        "question": question,
        "gap_field": top_gap["field"],
        "gap_type": top_gap["gap_type"]
    }

# Quick test
# if __name__ == "__main__":
#     test_persona = {
#         "name": "Bilal",
#         "profession": "",
#         "city": "Lahore",
#         "hobbies": ["cricket"],
#         "goals": [],
#         "personality": "",
#         "background": "",
#         "updated_at": "2026-05-23T00:00:00+00:00"
#     }
#     result = next_question("test-user", test_persona)
#     print(f"Question: {result['question']}")
#     print(f"Gap field: {result['gap_field']}")
#     print(f"Gap type: {result['gap_type']}")