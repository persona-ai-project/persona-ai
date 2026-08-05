from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from core.security import get_current_user
import os, json, uuid, re
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/persona")
_engine = create_engine(DATABASE_URL)

router = APIRouter(prefix="/questions", tags=["questions"])


class NextQuestionResponse(BaseModel):
    user_id: str
    question: str
    gap_field: str
    gap_type: str


class AnswerRequest(BaseModel):
    user_id: str
    question: str
    answer: str


EXTRACT_PROMPT = """You extract persona data from a Q&A pair. Return ONLY valid JSON.

Question: {question}
Answer: {answer}

Return a JSON object with ONLY the fields that can be inferred. Use these keys:
- "name" (string): real name if mentioned
- "profession" (string): job/role
- "hobbies" (string[]): interests
- "goals" (string[]): what they want
- "personality" (string): personality description
- "background" (string): life context
- "voice" (object with keys: tone, style, catchphrases)
- "opinions" (object of topic -> opinion string)
- "topics" (string[]): things they like to discuss
- "quirks" (string[]): unique habits
- "identity" (object with keys: name, age, location, occupation)
- "knowledge_anchors" (string[]): expertise areas
- "boundaries" (string[]): topics to avoid

Return ONLY the JSON object, no explanation."""


def _extract_persona_from_answer(question: str, answer: str) -> dict:
    """Use LLM to extract persona fields from a Q&A pair. Falls back to simple extraction."""
    try:
        from llm.router import chat_completion

        messages = [
            {"role": "system", "content": "You extract structured persona data. Return only valid JSON."},
            {"role": "user", "content": EXTRACT_PROMPT.format(question=question, answer=answer)}
        ]
        response = chat_completion(messages, max_tokens=512)
        content = response if isinstance(response, str) else response.get("content", "")
        content = content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        return json.loads(content)
    except Exception as e:
        print(f"[questions] LLM persona extraction failed, using fallback: {e}")
        return _simple_extract(question, answer)


def _simple_extract(question: str, answer: str) -> dict:
    """Keyword-based fallback extraction when no LLM is available."""
    extracted = {}
    q_lower = question.lower()
    a_clean = answer.strip()

    if any(w in q_lower for w in ["name", "who are you", "what's your name"]):
        words = a_clean.split()
        if len(words) >= 1 and words[0][0].isupper():
            extracted["name"] = a_clean.rstrip(".")
            extracted["identity"] = {"name": a_clean.rstrip(".")}
    elif any(w in q_lower for w in ["job", "work", "do you do", "profession", "studying", "working"]):
        extracted["profession"] = a_clean.rstrip(".")
        extracted["identity"] = {"occupation": a_clean.rstrip(".")}
    elif any(w in q_lower for w in ["passion", "interested", "hobby", "love", "enjoy"]):
        items = re.split(r',| and ', a_clean)
        extracted["hobbies"] = [i.strip().rstrip(".") for i in items if i.strip()]
        extracted["topics"] = [i.strip().rstrip(".") for i in items if i.strip()]
    elif any(w in q_lower for w in ["personality", "describe yourself", "describe your personality"]):
        extracted["personality"] = a_clean.rstrip(".")
    elif any(w in q_lower for w in ["goal", "working towards", "aim", "want to"]):
        extracted["goals"] = [a_clean.rstrip(".")]
    elif any(w in q_lower for w in ["opinion", "think about", "believe", "feel about"]):
        extracted["opinions"] = {a_clean[:50]: a_clean.rstrip(".")}
    elif any(w in q_lower for w in ["quirk", "unusual", "weird", "unique"]):
        extracted["quirks"] = [a_clean.rstrip(".")]
    elif any(w in q_lower for w in ["background", "where are you from", "grow up", "story"]):
        extracted["background"] = a_clean.rstrip(".")
    elif any(w in q_lower for w in ["boundary", "avoid", "don't like", "uncomfortable"]):
        extracted["boundaries"] = [a_clean.rstrip(".")]
    else:
        extracted["background"] = a_clean.rstrip(".")

    return extracted


def _get_persona_blob(user_id: str) -> dict:
    """Get current persona blob for user."""
    with _engine.connect() as conn:
        row = conn.execute(
            text("SELECT persona_blob FROM personas WHERE user_id = :uid AND is_active = true ORDER BY created_at DESC LIMIT 1"),
            {"uid": user_id}
        ).fetchone()
    if row and row[0]:
        blob = row[0]
        if isinstance(blob, str):
            blob = json.loads(blob)
        return blob
    return {"user_id": user_id, "name": "", "profession": "", "hobbies": [], "goals": [], "personality": "", "background": ""}


def _update_persona(user_id: str, extracted: dict):
    """Merge extracted fields into existing persona and upsert."""
    if not extracted:
        return

    existing = _get_persona_blob(user_id)

    for key, value in extracted.items():
        if not value:
            continue
        existing_val = existing.get(key)
        if isinstance(value, list):
            if isinstance(existing_val, list):
                merged = list(existing_val)
                for item in value:
                    if item not in merged:
                        merged.append(item)
                existing[key] = merged
            else:
                existing[key] = value
        elif isinstance(value, dict):
            if isinstance(existing_val, dict):
                merged = {**existing_val, **value}
                existing[key] = merged
            else:
                existing[key] = value
        elif isinstance(value, str) and value.strip():
            if not existing_val or (isinstance(existing_val, str) and not existing_val.strip()):
                existing[key] = value
            elif isinstance(existing_val, str) and value.lower() not in existing_val.lower():
                existing[key] = f"{existing_val.rstrip('.')}. {value}"

    existing["updated_at"] = datetime.now(timezone.utc).isoformat()

    with _engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM personas WHERE user_id = :uid AND is_active = true ORDER BY created_at DESC LIMIT 1"),
            {"uid": user_id}
        ).fetchone()

        if row:
            persona_id = str(row[0])
            conn.execute(
                text("UPDATE personas SET name = :name, persona_blob = :blob WHERE id = :id"),
                {"name": existing.get("name", ""), "blob": json.dumps(existing), "id": persona_id}
            )
            conn.execute(
                text("""INSERT INTO persona_versions (id, persona_id, user_id, version_number, persona_blob, created_at)
                         VALUES (:id, :pid, :uid, (SELECT COALESCE(MAX(version_number), 0) + 1 FROM persona_versions WHERE persona_id = :pid), :blob, :now)"""),
                {"id": str(uuid.uuid4()), "pid": persona_id, "uid": user_id, "blob": json.dumps(existing), "now": datetime.now(timezone.utc)}
            )
        else:
            persona_id = str(uuid.uuid4())
            conn.execute(
                text("""INSERT INTO personas (id, user_id, name, persona_blob, created_at, is_active)
                         VALUES (:id, :uid, :name, :blob, :now, true)"""),
                {"id": persona_id, "uid": user_id, "name": existing.get("name", ""), "blob": json.dumps(existing), "now": datetime.now(timezone.utc)}
            )
            conn.execute(
                text("""INSERT INTO persona_versions (id, persona_id, user_id, version_number, persona_blob, created_at)
                         VALUES (:id, :pid, :uid, 1, :blob, :now)"""),
                {"id": str(uuid.uuid4()), "pid": persona_id, "uid": user_id, "blob": json.dumps(existing), "now": datetime.now(timezone.utc)}
            )
        conn.commit()

    print(f"[questions] Updated persona for user {user_id} with fields: {list(extracted.keys())}")


@router.post("/answer")
def submit_answer(request: AnswerRequest, current_user: dict = Depends(get_current_user)):
    """
    Submit answer to a question.
    grade_answer checks if answer is substantive.
    If not — returns same question again.
    """
    try:
        from services.ai.questions.grade_answer import grade_answer

        grade = grade_answer(request.question, request.answer)

        if grade["substantive"]:
            # Index answer into Qdrant
            try:
                from services.ai.rag.retriever import index
                from shared.contracts.chunk import Chunk

                chunk = Chunk(
                    text=f"Q: {request.question} A: {request.answer}",
                    source="interview",
                    source_id=f"{request.user_id}_{request.question[:20]}",
                    created_at=datetime.now(timezone.utc),
                    metadata={}
                )
                index(request.user_id, [chunk])
                print(f"[questions] Indexed answer for user {request.user_id}")
            except Exception as e:
                print(f"[questions] Index warning: {e}")

            # Extract persona fields from Q&A and update persona
            try:
                extracted = _extract_persona_from_answer(request.question, request.answer)
                _update_persona(request.user_id, extracted)
            except Exception as e:
                print(f"[questions] Persona update warning: {e}")

            return {
                "accepted": True,
                "reason": grade["reason"],
                "message": "Answer accepted!"
            }
        else:
            return {
                "accepted": False,
                "reason": grade["reason"],
                "message": "Please give a more detailed answer!",
                "retry_question": request.question
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/starter")
def get_starter_questions(current_user: dict = Depends(get_current_user)):
    """
    Return the 5 hand-curated starter questions for onboarding.
    """
    from services.ai.questions.question_engine import STARTER_QUESTIONS
    return {"questions": STARTER_QUESTIONS}


@router.post("/next", response_model=NextQuestionResponse)
def get_next_question(user_id: str, persona_json: dict, current_user: dict = Depends(get_current_user)):
    """
    Generate the next interview question based on persona gaps.
    """
    try:
        from services.ai.questions.question_engine import next_question
        result = next_question(user_id, persona_json)
        return NextQuestionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
