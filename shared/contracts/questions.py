from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class NextQuestionRequest(BaseModel):
    """Input to QuestionEngine.next_question()"""
    model_config = ConfigDict(frozen=True)

    user_id: str
    persona_json: dict


class NextQuestionResponse(BaseModel):
    """Output of QuestionEngine.next_question()"""
    model_config = ConfigDict(frozen=True)

    user_id: str
    question: str
    gap_field: str
    gap_type: str