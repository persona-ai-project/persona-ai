from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.ai.questions.question_engine import next_question, STARTER_QUESTIONS
from fastapi import APIRouter, HTTPException, Depends
from core.security import get_current_user

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
                from datetime import datetime, timezone

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
    return {"questions": STARTER_QUESTIONS}


@router.post("/next", response_model=NextQuestionResponse)
def get_next_question(user_id: str, persona_json: dict, current_user: dict = Depends(get_current_user)):
    """
    Generate the next interview question based on persona gaps.
    """
    try:
        result = next_question(user_id, persona_json)
        return NextQuestionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))