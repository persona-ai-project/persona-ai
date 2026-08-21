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

router = APIRouter(prefix="/persona", tags=["persona"])


class PersonaUpdate(BaseModel):
    name: str | None = None
    profession: str | None = None
    hobbies: list[str] | None = None
    goals: list[str] | None = None
    personality: str | None = None
    background: str | None = None
    voice: dict | None = None
    opinions: dict | None = None
    topics: list[str] | None = None
    quirks: list[str] | None = None
    identity: dict | None = None
    knowledge_anchors: list[str] | None = None
    boundaries: list[str] | None = None


def _get_persona(conn, user_id: str):
    row = conn.execute(
        text("SELECT id, user_id, name, persona_blob, created_at, is_active FROM personas WHERE user_id = :uid AND is_active = true ORDER BY created_at DESC LIMIT 1"),
        {"uid": user_id}
    ).fetchone()
    return row


def _upsert_persona(conn, user_id: str, data: dict):
    existing = _get_persona(conn, user_id)
    now = datetime.now(timezone.utc)

    if existing:
        persona_id = str(existing[0])
        conn.execute(
            text("UPDATE personas SET name = :name, persona_blob = :blob WHERE id = :id"),
            {"name": data.get("name", ""), "blob": str(__import__('json').dumps(data)), "id": persona_id}
        )
        conn.execute(
            text("""INSERT INTO persona_versions (id, persona_id, user_id, version_number, persona_blob, created_at)
                     VALUES (:id, :pid, :uid, (SELECT COALESCE(MAX(version_number), 0) + 1 FROM persona_versions WHERE persona_id = :pid), :blob, :now)"""),
            {"id": str(uuid.uuid4()), "pid": persona_id, "uid": user_id, "blob": str(__import__('json').dumps(data)), "now": now}
        )
    else:
        persona_id = str(uuid.uuid4())
        conn.execute(
            text("""INSERT INTO personas (id, user_id, name, persona_blob, created_at, is_active)
                     VALUES (:id, :uid, :name, :blob, :now, true)"""),
            {"id": persona_id, "uid": user_id, "name": data.get("name", ""), "blob": str(__import__('json').dumps(data)), "now": now}
        )
        conn.execute(
            text("""INSERT INTO persona_versions (id, persona_id, user_id, version_number, persona_blob, created_at)
                     VALUES (:id, :pid, :uid, 1, :blob, :now)"""),
            {"id": str(uuid.uuid4()), "pid": persona_id, "uid": user_id, "blob": str(__import__('json').dumps(data)), "now": now}
        )
    return persona_id


@router.get("/{user_id}")
def get_persona(user_id: str, current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        with _engine.connect() as conn:
            row = _get_persona(conn, user_id)

        if row and row[3]:
            import json
            blob = row[3]
            if isinstance(blob, str):
                blob = json.loads(blob)
            blob["user_id"] = user_id
            return blob

        return {
            "user_id": user_id,
            "name": "",
            "profession": "",
            "hobbies": [],
            "goals": [],
            "personality": "",
            "background": "",
            "updated_at": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{user_id}")
def update_persona(user_id: str, body: PersonaUpdate, current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        import json
        with _engine.connect() as conn:
            row = _get_persona(conn, user_id)

            if row and row[3]:
                existing = row[3]
                if isinstance(existing, str):
                    existing = json.loads(existing)
            else:
                existing = {
                    "user_id": user_id, "name": "", "profession": "",
                    "hobbies": [], "goals": [], "personality": "", "background": ""
                }

            update_data = update.model_dump(exclude_none=True)
            existing.update(update_data)
            existing["updated_at"] = datetime.now(timezone.utc).isoformat()

            _upsert_persona(conn, user_id, existing)
            conn.commit()

        return {"message": "Persona updated!", "persona": existing}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/completeness")
def get_completeness(user_id: str, current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        import json
        with _engine.connect() as conn:
            row = _get_persona(conn, user_id)

        if not row or not row[3]:
            return {"user_id": user_id, "completeness": 0, "breakdown": {}}

        blob = row[3]
        if isinstance(blob, str):
            blob = json.loads(blob)

        scores = {
            "identity": 0.15 if blob.get("identity") and (isinstance(blob["identity"], dict) and any(v for v in blob["identity"].values() if v)) else 0,
            "voice": 0.20 if blob.get("voice") else 0,
            "opinions": 0.15 if blob.get("opinions") else 0,
            "topics": 0.10 if blob.get("topics") else 0,
            "quirks": 0.10 if blob.get("quirks") else 0,
            "knowledge_anchors": 0.10 if blob.get("knowledge_anchors") else 0,
            "boundaries": 0.05 if blob.get("boundaries") else 0,
            "basics": 0.15 if (
                (blob.get("name") and isinstance(blob["name"], str) and blob["name"].strip()) or
                (blob.get("profession") and isinstance(blob["profession"], str) and blob["profession"].strip()) or
                (blob.get("hobbies") and isinstance(blob["hobbies"], list) and len(blob["hobbies"]) > 0) or
                (blob.get("personality") and isinstance(blob["personality"], str) and blob["personality"].strip())
            ) else 0,
        }

        total = sum(scores.values())
        return {"user_id": user_id, "completeness": round(total, 2), "breakdown": scores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/history")
def get_persona_history(user_id: str, current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        import json
        with _engine.connect() as conn:
            rows = conn.execute(
                text("""SELECT pv.id, pv.version_number, pv.persona_blob, pv.created_at
                         FROM persona_versions pv
                         JOIN personas p ON pv.persona_id = p.id
                         WHERE p.user_id = :uid
                         ORDER BY pv.version_number DESC LIMIT 20"""),
                {"uid": user_id}
            ).fetchall()

        versions = []
        for r in rows:
            blob = r[2]
            if isinstance(blob, str):
                blob = json.loads(blob)
            versions.append({
                "id": str(r[0]),
                "version": r[1],
                "persona": blob,
                "created_at": str(r[3])
            })
        return {"versions": versions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
def delete_persona(user_id: str, current_user: dict = Depends(get_current_user)):
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        with _engine.connect() as conn:
            conn.execute(
                text("UPDATE personas SET is_active = false WHERE user_id = :uid"),
                {"uid": user_id}
            )
            conn.commit()

        try:
            from services.ai.rag.retriever import delete as rag_delete
            rag_delete(user_id=user_id)
        except Exception as e:
            print(f"Qdrant delete warning: {e}")

        return {"message": f"Persona deleted for user {user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
