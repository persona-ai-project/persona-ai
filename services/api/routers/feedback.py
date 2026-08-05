import os
import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from core.security import get_current_user
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/persona")
_engine = create_engine(DATABASE_URL)

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    user_id: str
    message_id: str | None = None
    message: str
    twin_response: str
    kind: str  # "thumbs_up", "thumbs_down", "rewrite", "side_by_side"
    rewrite: str | None = None


class FeedbackResponse(BaseModel):
    status: str
    preference_pair_created: bool


@router.post("", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    try:
        with _engine.connect() as conn:
            conn.execute(
                text("""INSERT INTO feedback (id, user_id, message_id, rating, comment, created_at)
                         VALUES (:id, :user_id, :message_id, :rating, :comment, :now)"""),
                {
                    "id": str(uuid.uuid4()),
                    "user_id": request.user_id,
                    "message_id": request.message_id,
                    "rating": 1 if request.kind == "thumbs_up" else (-1 if request.kind == "thumbs_down" else 0),
                    "comment": request.rewrite if request.kind == "rewrite" else request.kind,
                    "now": datetime.now(timezone.utc),
                }
            )

            pair_created = False

            if request.kind == "rewrite" and request.rewrite:
                conn.execute(
                    text("""INSERT INTO preference_pairs (id, user_id, prompt, chosen, rejected, created_at)
                             VALUES (:id, :user_id, :prompt, :chosen, :rejected, :now)"""),
                    {
                        "id": str(uuid.uuid4()),
                        "user_id": request.user_id,
                        "prompt": request.message,
                        "chosen": request.rewrite,
                        "rejected": request.twin_response,
                        "now": datetime.now(timezone.utc),
                    }
                )
                pair_created = True

            conn.commit()

        return FeedbackResponse(status="ok", preference_pair_created=pair_created)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_feedback_stats(current_user: dict = Depends(get_current_user)):
    try:
        with _engine.connect() as conn:
            rows = conn.execute(
                text("SELECT rating, COUNT(*) FROM feedback WHERE user_id = :uid GROUP BY rating"),
                {"uid": current_user["user_id"]}
            ).fetchall()

            counts = {r[0]: r[1] for r in rows}
            thumbs_up = counts.get(1, 0)
            thumbs_down = counts.get(-1, 0)

            rewrites = conn.execute(
                text("SELECT COUNT(*) FROM feedback WHERE user_id = :uid AND comment IS NOT NULL AND rating = 0"),
                {"uid": current_user["user_id"]}
            ).scalar() or 0

            pairs_count = conn.execute(
                text("SELECT COUNT(*) FROM preference_pairs WHERE user_id = :uid"),
                {"uid": current_user["user_id"]}
            ).scalar() or 0

            pairs = conn.execute(
                text("SELECT prompt, chosen, rejected, created_at FROM preference_pairs WHERE user_id = :uid ORDER BY created_at DESC LIMIT 10"),
                {"uid": current_user["user_id"]}
            ).fetchall()

        return {
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down,
            "rewrites": rewrites,
            "preference_pairs": pairs_count,
            "pairs": [{"prompt": p[0], "chosen": p[1], "rejected": p[2], "created_at": str(p[3])} for p in pairs]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
