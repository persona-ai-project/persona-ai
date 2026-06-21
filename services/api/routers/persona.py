import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends
from core.security import get_current_user

# Load env
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from supabase import create_client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

router = APIRouter(prefix="/persona", tags=["persona"])

# In-memory store for demo
persona_store = {}


class PersonaUpdate(BaseModel):
    name: str | None = None
    profession: str | None = None
    hobbies: list[str] | None = None
    goals: list[str] | None = None
    personality: str | None = None
    background: str | None = None


@router.get("/{user_id}")
def get_persona(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get current persona for a user."""
    persona = persona_store.get(user_id, {
        "user_id": user_id,
        "name": "",
        "profession": "",
        "hobbies": [],
        "goals": [],
        "personality": "",
        "background": "",
        "updated_at": None
    })
    return persona


@router.patch("/{user_id}")
def update_persona(user_id: str, update: PersonaUpdate, current_user: dict = Depends(get_current_user)):
    """Update persona fields for a user."""
    from datetime import datetime, timezone

    # Get existing or create new
    persona = persona_store.get(user_id, {
        "user_id": user_id,
        "name": "",
        "profession": "",
        "hobbies": [],
        "goals": [],
        "personality": "",
        "background": "",
    })

    # Update only provided fields
    update_data = update.model_dump(exclude_none=True)
    persona.update(update_data)
    persona["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Save
    persona_store[user_id] = persona

    return {
        "message": "Persona updated!",
        "persona": persona
    }


@router.get("/{user_id}/completeness")
def get_completeness(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Calculate persona completeness score (0.0 to 1.0).
    Used for dashboard ring.
    """
    persona = persona_store.get(user_id, {})

    # Weighted scoring
    scores = {
        "name": 0.2 if persona.get("name") else 0,
        "profession": 0.2 if persona.get("profession") else 0,
        "hobbies": 0.2 if persona.get("hobbies") else 0,
        "goals": 0.2 if persona.get("goals") else 0,
        "personality": 0.1 if persona.get("personality") else 0,
        "background": 0.1 if persona.get("background") else 0,
    }

    total = sum(scores.values())

    return {
        "user_id": user_id,
        "completeness": round(total, 2),
        "breakdown": scores
    }


@router.delete("/{user_id}")
def delete_persona(user_id: str, current_user: dict = Depends(get_current_user)):
    """Delete persona and all associated data."""
    if user_id in persona_store:
        del persona_store[user_id]

    # Also delete from Qdrant
    try:
        from services.ai.rag.retriever import delete as rag_delete
        rag_delete(user_id=user_id)
    except Exception as e:
        print(f"Qdrant delete warning: {e}")

    return {"message": f"Persona deleted for user {user_id}"}