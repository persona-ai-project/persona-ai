from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from core.security import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])

# In-memory store for demo (real project mein database hoga)
feedback_store = []
preference_pairs = []


class FeedbackRequest(BaseModel):
    user_id: str
    message: str
    twin_response: str
    kind: str  # "thumbs_up", "thumbs_down", "rewrite"
    rewrite: str | None = None


class FeedbackResponse(BaseModel):
    status: str
    preference_pair_created: bool


@router.post("", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    """
    Submit feedback on twin response.
    On rewrite: creates a preference pair for DPO training.
    """
    try:
        # Save feedback
        feedback_store.append({
            "user_id": request.user_id,
            "message": request.message,
            "twin_response": request.twin_response,
            "kind": request.kind,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        pair_created = False

        # If rewrite — create preference pair
        if request.kind == "rewrite" and request.rewrite:
            preference_pairs.append({
                "user_id": request.user_id,
                "prompt": request.message,
                "chosen": request.rewrite,
                "rejected": request.twin_response,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            pair_created = True

        return FeedbackResponse(
            status="ok",
            preference_pair_created=pair_created
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_feedback_stats(current_user: dict = Depends(get_current_user)):
    """
    Get feedback statistics — shown on dashboard.
    """
    thumbs_up = sum(1 for f in feedback_store if f["kind"] == "thumbs_up")
    thumbs_down = sum(1 for f in feedback_store if f["kind"] == "thumbs_down")
    rewrites = sum(1 for f in feedback_store if f["kind"] == "rewrite")

    return {
        "thumbs_up": thumbs_up,
        "thumbs_down": thumbs_down,
        "rewrites": rewrites,
        "preference_pairs": len(preference_pairs),
        "pairs": preference_pairs  # show actual pairs for demo
    }