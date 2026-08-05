import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from services.ai.questions.assess_gaps import assess_gaps
from pathlib import Path


# Try multiple possible .env locations
for env_path in [
    Path(__file__).resolve().parents[1] / "rag" / ".env",
    Path(__file__).resolve().parents[3] / "services" / "api" / ".env",
]:
    if env_path.exists():
        load_dotenv(env_path)
        break
load_dotenv(env_path)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# Hand-curated starter questions for new users (onboarding)
STARTER_QUESTIONS = [
    "Hey! What's your name?",
    "What do you do — are you working, studying, or both?",
    "What are you passionate about or interested in?",
    "How would you describe your personality in a few words?",
    "What's one goal you're really working towards right now?"
]

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
    response = model.generate_content(prompt)
    question = response.text.strip()

    return {
        "user_id": user_id,
        "question": question,
        "gap_field": top_gap["field"],
        "gap_type": top_gap["gap_type"]
    }
