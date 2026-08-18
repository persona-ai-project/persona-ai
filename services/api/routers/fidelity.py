"""
routers/fidelity.py
===================
Fidelity evaluation API endpoints.

Routes:
    POST /twins/{twin_id}/fidelity/evaluate     — evaluate a single response
    POST /twins/{twin_id}/fidelity/batch        — evaluate multiple responses
    GET  /twins/{twin_id}/fidelity/history      — get evaluation history
    GET  /twins/{twin_id}/fidelity/summary      — get aggregate fidelity scores
    POST /twins/{twin_id}/fidelity/evaluate-chat — evaluate last chat response
"""
from __future__ import annotations

import os
import uuid
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from core.security import get_current_user

router = APIRouter(prefix="/twins", tags=["fidelity"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)


# ── Models ──────────────────────────────────────────────────────────────────────

class EvaluateRequest(BaseModel):
    response: str
    knowledge: list[str] = []
    sources_cited: int = 0


class EvaluateBatchRequest(BaseModel):
    responses: list[dict]  # List of {response: str, sources_cited?: int}
    knowledge: list[str] = []


class FidelityScoreResponse(BaseModel):
    overall: float
    grounding: float
    consistency: float
    hallucination: float
    personality: float
    confidence: float
    issues: list[str]
    suggestions: list[str]


class EvaluationResponse(BaseModel):
    score: FidelityScoreResponse
    knowledge_used: int
    knowledge_available: int
    sources_cited: int
    response_length: int
    evaluated_at: str


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _verify_twin_owner(conn, twin_id: str, user_id: str):
    """Verify user owns the twin."""
    row = conn.execute(
        text("SELECT id, owner_id FROM twins WHERE id = :id AND is_active = true"),
        {"id": twin_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Twin not found")
    if str(row[1]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return row


def _load_twin_knowledge(conn, twin_id: str, limit: int = 50) -> list[str]:
    """Load all knowledge items for a twin."""
    rows = conn.execute(
        text("""SELECT content FROM knowledge_items 
                WHERE twin_id = :tid AND is_active = true 
                ORDER BY confidence DESC 
                LIMIT :limit"""),
        {"tid": twin_id, "limit": limit}
    ).fetchall()
    return [r[0] for r in rows]


def _load_twin_personality(conn, twin_id: str) -> dict | None:
    """Load twin's personality configuration."""
    row = conn.execute(
        text("SELECT personality_config FROM twins WHERE id = :id"),
        {"id": twin_id}
    ).fetchone()
    return row[0] if row else None


def _save_evaluation(conn, twin_id: str, evaluation: dict):
    """Save evaluation result to database."""
    # Update twin's average fidelity score
    conn.execute(
        text("""UPDATE twins 
               SET avg_fidelity = COALESCE(
                   (SELECT AVG(score->>'overall')::float 
                    FROM jsonb_array_elements(
                        CASE WHEN metadata IS NULL THEN '[]'::jsonb 
                             ELSE metadata->'evaluations' END
                    ) AS score),
                   :score
               ),
               updated_at = :now
               WHERE id = :id"""),
        {"id": twin_id, "score": str(evaluation.get("overall", 0)), "now": datetime.now(timezone.utc)}
    )


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.post("/{twin_id}/fidelity/evaluate", response_model=EvaluationResponse)
def evaluate_response(
    twin_id: str,
    body: EvaluateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Evaluate a single twin response for fidelity."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        # Load knowledge if not provided
        knowledge = body.knowledge
        if not knowledge:
            knowledge = _load_twin_knowledge(db, twin_id)

        # Load personality config
        personality = _load_twin_personality(db, twin_id)

        # Run evaluation
        from services.ai.fidelity.evaluator import evaluate_fidelity
        result = evaluate_fidelity(
            response=body.response,
            knowledge=knowledge,
            personality_config=personality,
            sources_cited=body.sources_cited,
        )

        # Save evaluation
        _save_evaluation(db, twin_id, {
            "overall": result.score.overall,
            "grounding": result.score.grounding,
            "consistency": result.score.consistency,
            "hallucination": result.score.hallucination,
            "personality": result.score.personality,
        })

        db.commit()

        return EvaluationResponse(
            score=FidelityScoreResponse(**result.score.__dict__),
            knowledge_used=result.knowledge_used,
            knowledge_available=result.knowledge_available,
            sources_cited=result.sources_cited,
            response_length=result.response_length,
            evaluated_at=result.evaluated_at,
        )
    finally:
        db.close()


@router.post("/{twin_id}/fidelity/batch")
def evaluate_batch(
    twin_id: str,
    body: EvaluateBatchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Evaluate multiple twin responses."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        # Load knowledge if not provided
        knowledge = body.knowledge
        if not knowledge:
            knowledge = _load_twin_knowledge(db, twin_id)

        # Load personality config
        personality = _load_twin_personality(db, twin_id)

        # Run batch evaluation
        from services.ai.fidelity.evaluator import evaluate_response_batch
        results = evaluate_response_batch(
            responses=body.responses,
            knowledge=knowledge,
            personality_config=personality,
        )

        # Calculate aggregate
        from services.ai.fidelity.evaluator import calculate_twin_fidelity
        aggregate = calculate_twin_fidelity(results)

        # Save aggregate
        _save_evaluation(db, twin_id, aggregate)
        db.commit()

        return {
            "evaluations": [
                {
                    "score": r.score.__dict__,
                    "knowledge_used": r.knowledge_used,
                    "sources_cited": r.sources_cited,
                    "response_length": r.response_length,
                }
                for r in results
            ],
            "aggregate": aggregate,
        }
    finally:
        db.close()


@router.get("/{twin_id}/fidelity/summary")
def get_fidelity_summary(
    twin_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get aggregate fidelity scores for a twin."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        # Get twin's current fidelity
        twin = db.execute(
            text("""SELECT avg_fidelity, total_chats, total_messages 
                    FROM twins WHERE id = :id"""),
            {"id": twin_id}
        ).fetchone()

        # Get recent feedback scores
        feedback = db.execute(
            text("""SELECT AVG(rating)::float as avg_rating, COUNT(*) as total
                    FROM feedback f
                    JOIN messages m ON f.message_id = m.id
                    WHERE m.persona_id = :tid"""),
            {"tid": twin_id}
        ).fetchone()

        # Get knowledge stats
        knowledge_stats = db.execute(
            text("""SELECT content_type, COUNT(*), AVG(confidence)::float
                    FROM knowledge_items
                    WHERE twin_id = :tid AND is_active = true
                    GROUP BY content_type"""),
            {"tid": twin_id}
        ).fetchall()

        # Get source stats
        source_stats = db.execute(
            text("""SELECT status, COUNT(*)
                    FROM sources
                    WHERE twin_id = :tid
                    GROUP BY status"""),
            {"tid": twin_id}
        ).fetchall()

        return {
            "twin_id": twin_id,
            "avg_fidelity": twin[0] if twin else 0,
            "total_chats": twin[1] if twin else 0,
            "total_messages": twin[2] if twin else 0,
            "feedback": {
                "avg_rating": round(feedback[0], 2) if feedback and feedback[0] else 0,
                "total_reviews": feedback[1] if feedback else 0,
            },
            "knowledge": {
                "total_items": sum(s[1] for s in knowledge_stats),
                "by_type": {s[0]: {"count": s[1], "avg_confidence": round(s[2], 2)} for s in knowledge_stats},
                "total_sources": sum(s[1] for s in source_stats),
                "sources_by_status": {s[0]: s[1] for s in source_stats},
            },
            "fidelity_factors": {
                "knowledge_coverage": min(len(knowledge_stats) / 7, 1.0),  # 7 knowledge types
                "source_diversity": min(sum(s[1] for s in source_stats) / 5, 1.0),  # 5 source types
                "confidence_level": round(sum(s[2] * s[1] for s in knowledge_stats) / max(sum(s[1] for s in knowledge_stats), 1), 2),
            },
        }
    finally:
        db.close()


@router.get("/{twin_id}/fidelity/history")
def get_fidelity_history(
    twin_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
):
    """Get recent evaluation history for a twin."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        # Get recent messages with feedback
        messages = db.execute(
            text("""SELECT m.id, m.content, m.created_at,
                           f.rating, f.comment
                    FROM messages m
                    LEFT JOIN feedback f ON m.id = f.message_id
                    WHERE m.persona_id = :tid AND m.role = 'assistant'
                    ORDER BY m.created_at DESC
                    LIMIT :limit"""),
            {"tid": twin_id, "limit": limit}
        ).fetchall()

        # Evaluate each response
        knowledge = _load_twin_knowledge(db, twin_id, limit=20)
        personality = _load_twin_personality(db, twin_id)

        from services.ai.fidelity.evaluator import evaluate_fidelity

        history = []
        for msg in messages:
            result = evaluate_fidelity(
                response=msg[1],
                knowledge=knowledge,
                personality_config=personality,
            )
            history.append({
                "message_id": str(msg[0]),
                "response_preview": msg[1][:100] + "..." if len(msg[1]) > 100 else msg[1],
                "score": result.score.__dict__,
                "user_rating": msg[3],
                "user_comment": msg[4],
                "created_at": str(msg[2]),
            })

        return {"history": history, "total": len(history)}
    finally:
        db.close()


@router.post("/{twin_id}/fidelity/evaluate-chat")
def evaluate_last_chat(
    twin_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Evaluate the last chat response from a twin."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        # Get last assistant message
        msg = db.execute(
            text("""SELECT id, content, created_at
                    FROM messages
                    WHERE persona_id = :tid AND role = 'assistant'
                    ORDER BY created_at DESC LIMIT 1"""),
            {"tid": twin_id}
        ).fetchone()

        if not msg:
            raise HTTPException(status_code=404, detail="No chat messages found")

        # Load knowledge and personality
        knowledge = _load_twin_knowledge(db, twin_id)
        personality = _load_twin_personality(db, twin_id)

        # Run evaluation
        from services.ai.fidelity.evaluator import evaluate_fidelity
        result = evaluate_fidelity(
            response=msg[1],
            knowledge=knowledge,
            personality_config=personality,
        )

        # Save
        _save_evaluation(db, twin_id, {"overall": result.score.overall})
        db.commit()

        return {
            "message_id": str(msg[0]),
            "response_preview": msg[1][:200],
            "evaluation": result.__dict__,
        }
    finally:
        db.close()


from sqlalchemy.orm import sessionmaker
