import os
import uuid
import re
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from core.security import get_current_user
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/persona")
_engine = create_engine(DATABASE_URL)

router = APIRouter(prefix="/twins", tags=["twins"])


def _auto_activate_twin(conn, twin_id: str):
    """Auto-activate a twin if it has knowledge items. Called after interview/source ingestion."""
    count = conn.execute(
        text("""SELECT COUNT(*) FROM knowledge_items
                WHERE twin_id = :tid AND is_active = true"""),
        {"tid": twin_id}
    ).scalar()
    if count and count > 0:
        conn.execute(
            text("""UPDATE twins SET status = 'active', updated_at = :now
                    WHERE id = :tid AND status = 'draft'"""),
            {"tid": twin_id, "now": datetime.now(timezone.utc)}
        )


def _slugify(name: str) -> str:
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


class TwinCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    tagline: str | None = Field(None, max_length=200)
    bio: str | None = None
    category_id: str | None = None
    is_public_figure: bool = False
    public_figure_name: str | None = None
    personality_config: dict | None = None
    boundaries: dict | None = None
    knowledge_anchors: dict | None = None


class TwinUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    tagline: str | None = Field(None, max_length=200)
    bio: str | None = None
    category_id: str | None = None
    is_public_figure: bool | None = None
    public_figure_name: str | None = None
    personality_config: dict | None = None
    boundaries: dict | None = None
    knowledge_anchors: dict | None = None
    visibility: str | None = None
    status: str | None = None


class TwinResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    slug: str
    tagline: str | None
    bio: str | None
    avatar_url: str | None
    cover_url: str | None
    category_id: str | None
    is_public_figure: bool
    verification_level: str
    status: str
    visibility: str
    total_chats: int
    total_messages: int
    avg_fidelity: float | None
    created_at: str
    updated_at: str


def _get_user_subscription(conn, user_id: str):
    row = conn.execute(
        text("""SELECT us.id, us.plan_id, sp.name as plan_name, sp.max_twins, us.twins_used
                FROM user_subscriptions us
                JOIN subscription_plans sp ON us.plan_id = sp.id
                WHERE us.user_id = :uid AND us.status = 'active'"""),
        {"uid": user_id}
    ).fetchone()
    return row


def _check_twin_limit(conn, user_id: str):
    sub = _get_user_subscription(conn, user_id)
    if not sub:
        raise HTTPException(status_code=403, detail="No active subscription")
    
    plan_name, max_twins, twins_used = sub[2], sub[3], sub[4]
    if twins_used >= max_twins:
        raise HTTPException(
            status_code=403,
            detail=f"Twin limit reached ({max_twins}) for {plan_name} plan. Upgrade to create more twins."
        )
    return sub


@router.post("", response_model=TwinResponse)
def create_twin(twin: TwinCreate, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    try:
        with _engine.connect() as conn:
            # Check twin limit (disabled for now — unlimited twins)
            # _check_twin_limit(conn, user_id)
            
            # Generate slug
            slug = _slugify(twin.name)
            
            # Check slug uniqueness
            existing = conn.execute(
                text("SELECT id FROM twins WHERE slug = :slug"),
                {"slug": slug}
            ).fetchone()
            if existing:
                slug = f"{slug}-{str(uuid.uuid4())[:8]}"
            
            # Validate category if provided
            if twin.category_id:
                cat = conn.execute(
                    text("SELECT id FROM twin_categories WHERE id = :id AND is_active = true"),
                    {"id": twin.category_id}
                ).fetchone()
                if not cat:
                    raise HTTPException(status_code=400, detail="Invalid category")
            
            # Create twin
            twin_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            conn.execute(
                text("""INSERT INTO twins 
                    (id, owner_id, category_id, name, slug, tagline, bio, 
                     is_public_figure, public_figure_name, personality_config, 
                     boundaries, knowledge_anchors, status, visibility, created_at, updated_at)
                    VALUES 
                    (:id, :owner_id, :category_id, :name, :slug, :tagline, :bio,
                     :is_public_figure, :public_figure_name, :personality_config,
                     :boundaries, :knowledge_anchors, :status, :visibility, :created_at, :updated_at)"""),
                {
                    "id": twin_id,
                    "owner_id": user_id,
                    "category_id": twin.category_id,
                    "name": twin.name,
                    "slug": slug,
                    "tagline": twin.tagline,
                    "bio": twin.bio,
                    "is_public_figure": twin.is_public_figure,
                    "public_figure_name": twin.public_figure_name,
                    "personality_config": twin.personality_config,
                    "boundaries": twin.boundaries,
                    "knowledge_anchors": twin.knowledge_anchors,
                    "status": "draft",
                    "visibility": "private",
                    "created_at": now,
                    "updated_at": now,
                }
            )
            
            # Increment twins_used
            conn.execute(
                text("""UPDATE user_subscriptions 
                       SET twins_used = twins_used + 1 
                       WHERE user_id = :uid AND status = 'active'"""),
                {"uid": user_id}
            )
            
            conn.commit()
            
            return TwinResponse(
                id=twin_id,
                owner_id=user_id,
                name=twin.name,
                slug=slug,
                tagline=twin.tagline,
                bio=twin.bio,
                avatar_url=None,
                cover_url=None,
                category_id=twin.category_id,
                is_public_figure=twin.is_public_figure,
                verification_level="unverified",
                status="draft",
                visibility="private",
                total_chats=0,
                total_messages=0,
                avg_fidelity=None,
                created_at=now.isoformat(),
                updated_at=now.isoformat(),
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
def list_twins(
    current_user: dict = Depends(get_current_user),
    status: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    user_id = current_user["user_id"]
    
    try:
        with _engine.connect() as conn:
            query = """
                SELECT t.id, t.name, t.slug, t.tagline, t.status, t.visibility,
                       t.total_chats, t.avg_fidelity, t.created_at, t.updated_at,
                       tc.name as category_name
                FROM twins t
                LEFT JOIN twin_categories tc ON t.category_id = tc.id
                WHERE t.owner_id = :uid AND t.is_active = true
            """
            params = {"uid": user_id, "limit": limit, "offset": offset}
            
            if status:
                query += " AND t.status = :status"
                params["status"] = status
            
            query += " ORDER BY t.created_at DESC LIMIT :limit OFFSET :offset"
            
            rows = conn.execute(text(query), params).fetchall()
            
            # Get total count
            count_query = "SELECT COUNT(*) FROM twins WHERE owner_id = :uid AND is_active = true"
            count_params = {"uid": user_id}
            if status:
                count_query += " AND status = :status"
                count_params["status"] = status
            
            total = conn.execute(text(count_query), count_params).scalar()
            
            twins = []
            for r in rows:
                twins.append({
                    "id": str(r[0]),
                    "name": r[1],
                    "slug": r[2],
                    "tagline": r[3],
                    "status": r[4],
                    "visibility": r[5],
                    "total_chats": r[6],
                    "avg_fidelity": r[7],
                    "created_at": str(r[8]),
                    "updated_at": str(r[9]),
                    "category_name": r[10],
                })
            
            return {"twins": twins, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{twin_id}")
def get_twin(twin_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    try:
        with _engine.connect() as conn:
            row = conn.execute(
                text("""SELECT t.*, tc.name as category_name
                        FROM twins t
                        LEFT JOIN twin_categories tc ON t.category_id = tc.id
                        WHERE t.id = :id AND t.owner_id = :uid AND t.is_active = true"""),
                {"id": twin_id, "uid": user_id}
            ).fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Twin not found")
            
            # Get knowledge stats
            knowledge_stats = conn.execute(
                text("""SELECT content_type, COUNT(*) 
                        FROM knowledge_items 
                        WHERE twin_id = :tid AND is_active = true 
                        GROUP BY content_type"""),
                {"tid": twin_id}
            ).fetchall()
            
            # Get source stats
            source_stats = conn.execute(
                text("""SELECT status, COUNT(*) 
                        FROM sources 
                        WHERE twin_id = :tid 
                        GROUP BY status"""),
                {"tid": twin_id}
            ).fetchall()
            
            # Get interview stats
            interview_stats = conn.execute(
                text("""SELECT status, COUNT(*) 
                        FROM interview_sessions 
                        WHERE twin_id = :tid 
                        GROUP BY status"""),
                {"tid": twin_id}
            ).fetchall()
            
            # Use column names from the result proxy
            cols = row._mapping
            return {
                "id": str(cols["id"]),
                "owner_id": str(cols["owner_id"]),
                "category_id": str(cols["category_id"]) if cols.get("category_id") else None,
                "name": cols["name"],
                "slug": cols["slug"],
                "tagline": cols.get("tagline"),
                "bio": cols.get("bio"),
                "avatar_url": cols.get("avatar_url"),
                "cover_url": cols.get("cover_url"),
                "is_public_figure": cols.get("is_public_figure", False),
                "public_figure_name": cols.get("public_figure_name"),
                "verification_level": cols.get("verification_level", "unverified"),
                "personality_config": cols.get("personality_config"),
                "boundaries": cols.get("boundaries"),
                "knowledge_anchors": cols.get("knowledge_anchors"),
                "status": cols.get("status", "draft"),
                "visibility": cols.get("visibility", "private"),
                "total_chats": cols.get("total_chats", 0),
                "total_messages": cols.get("total_messages", 0),
                "avg_fidelity": cols.get("avg_fidelity"),
                "metadata": cols.get("metadata"),
                "created_at": str(cols["created_at"]),
                "updated_at": str(cols["updated_at"]),
                "is_active": cols.get("is_active", True),
                "category_name": cols.get("category_name"),
                "knowledge_stats": {r[0]: r[1] for r in knowledge_stats},
                "source_stats": {r[0]: r[1] for r in source_stats},
                "interview_stats": {r[0]: r[1] for r in interview_stats},
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{twin_id}", response_model=TwinResponse)
def update_twin(twin_id: str, update: TwinUpdate, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    try:
        with _engine.connect() as conn:
            # Verify ownership
            existing = conn.execute(
                text("SELECT id, name, slug FROM twins WHERE id = :id AND owner_id = :uid AND is_active = true"),
                {"id": twin_id, "uid": user_id}
            ).fetchone()
            
            if not existing:
                raise HTTPException(status_code=404, detail="Twin not found")
            
            # Build update query dynamically
            updates = []
            params = {"id": twin_id}
            
            for field, value in update.model_dump(exclude_none=True).items():
                if field == "name" and value:
                    # Regenerate slug if name changes
                    new_slug = _slugify(value)
                    slug_check = conn.execute(
                        text("SELECT id FROM twins WHERE slug = :slug AND id != :id"),
                        {"slug": new_slug, "id": twin_id}
                    ).fetchone()
                    if slug_check:
                        new_slug = f"{new_slug}-{str(uuid.uuid4())[:8]}"
                    updates.append("slug = :slug")
                    params["slug"] = new_slug
                
                if field == "visibility" and value not in ["private", "unlisted", "public"]:
                    raise HTTPException(status_code=400, detail="Invalid visibility")
                
                if field == "status" and value not in ["draft", "active", "archived", "suspended"]:
                    raise HTTPException(status_code=400, detail="Invalid status")
                
                updates.append(f"{field} = :{field}")
                params[field] = value
            
            if not updates:
                raise HTTPException(status_code=400, detail="No updates provided")
            
            updates.append("updated_at = :updated_at")
            params["updated_at"] = datetime.now(timezone.utc)
            
            conn.execute(
                text(f"UPDATE twins SET {', '.join(updates)} WHERE id = :id"),
                params
            )
            conn.commit()
            
            # Fetch updated twin
            row = conn.execute(
                text("SELECT * FROM twins WHERE id = :id"),
                {"id": twin_id}
            ).fetchone()
            
            return TwinResponse(
                id=str(row[0]),
                owner_id=str(row[1]),
                name=row[3],
                slug=row[4],
                tagline=row[5],
                bio=row[6],
                avatar_url=row[7],
                cover_url=row[8],
                category_id=str(row[2]) if row[2] else None,
                is_public_figure=row[9],
                verification_level=row[11],
                status=row[15],
                visibility=row[16],
                total_chats=row[17],
                total_messages=row[18],
                avg_fidelity=row[19],
                created_at=str(row[21]),
                updated_at=str(row[22]),
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{twin_id}")
def delete_twin(twin_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    
    try:
        with _engine.connect() as conn:
            # Verify ownership
            existing = conn.execute(
                text("SELECT id FROM twins WHERE id = :id AND owner_id = :uid AND is_active = true"),
                {"id": twin_id, "uid": user_id}
            ).fetchone()
            
            if not existing:
                raise HTTPException(status_code=404, detail="Twin not found")
            
            # Soft delete
            conn.execute(
                text("UPDATE twins SET is_active = false, updated_at = :now WHERE id = :id"),
                {"id": twin_id, "now": datetime.now(timezone.utc)}
            )
            
            # Decrement twins_used
            conn.execute(
                text("""UPDATE user_subscriptions 
                       SET twins_used = GREATEST(twins_used - 1, 0) 
                       WHERE user_id = :uid AND status = 'active'"""),
                {"uid": user_id}
            )
            
            conn.commit()
            
            # Clean up Qdrant vectors
            try:
                from services.ai.rag.retriever import delete_by_twin
                delete_by_twin(twin_id=twin_id)
            except Exception as e:
                print(f"Qdrant cleanup warning: {e}")
            
            return {"message": "Twin deleted", "id": twin_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/list")
def list_categories():
    try:
        with _engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id, name, slug, description, icon FROM twin_categories WHERE is_active = true ORDER BY name")
            ).fetchall()
            
            return {"categories": [
                {
                    "id": str(r[0]),
                    "name": r[1],
                    "slug": r[2],
                    "description": r[3],
                    "icon": r[4],
                }
                for r in rows
            ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public/{slug}")
def get_public_twin(slug: str):
    """Get a public twin profile (no auth required)"""
    try:
        with _engine.connect() as conn:
            row = conn.execute(
                text("""SELECT t.id, t.name, t.slug, t.tagline, t.bio, t.avatar_url,
                               t.cover_url, t.verification_level, t.total_chats,
                               t.avg_fidelity, t.created_at, tc.name as category_name
                        FROM twins t
                        LEFT JOIN twin_categories tc ON t.category_id = tc.id
                        WHERE t.slug = :slug AND t.visibility = 'public' AND t.status = 'active' AND t.is_active = true"""),
                {"slug": slug}
            ).fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Twin not found")
            
            return {
                "id": str(row[0]),
                "name": row[1],
                "slug": row[2],
                "tagline": row[3],
                "bio": row[4],
                "avatar_url": row[5],
                "cover_url": row[6],
                "verification_level": row[7],
                "total_chats": row[8],
                "avg_fidelity": row[9],
                "created_at": str(row[10]),
                "category_name": row[11],
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public")
def list_public_twins(
    category: str | None = None,
    search: str | None = None,
    sort: str = "popular",
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    """List public twins (no auth required)."""
    try:
        with _engine.connect() as conn:
            query = """
                SELECT t.id, t.name, t.slug, t.tagline, t.bio, t.avatar_url,
                       t.verification_level, t.total_chats, t.avg_fidelity,
                       t.created_at, tc.name as category_name
                FROM twins t
                LEFT JOIN twin_categories tc ON t.category_id = tc.id
                WHERE t.visibility = 'public' AND t.status = 'active' AND t.is_active = true
            """
            params = {"limit": limit, "offset": offset}

            if category:
                query += " AND tc.slug = :category"
                params["category"] = category

            if search:
                query += " AND (t.name ILIKE :search OR t.tagline ILIKE :search)"
                params["search"] = f"%{search}%"

            # Sorting
            if sort == "popular":
                query += " ORDER BY t.total_chats DESC"
            elif sort == "newest":
                query += " ORDER BY t.created_at DESC"
            elif sort == "rating":
                query += " ORDER BY t.avg_fidelity DESC NULLS LAST"
            else:
                query += " ORDER BY t.total_chats DESC"

            query += " LIMIT :limit OFFSET :offset"

            rows = conn.execute(text(query), params).fetchall()

            # Get total count
            count_query = """
                SELECT COUNT(*) FROM twins t
                LEFT JOIN twin_categories tc ON t.category_id = tc.id
                WHERE t.visibility = 'public' AND t.status = 'active' AND t.is_active = true
            """
            count_params = {}
            if category:
                count_query += " AND tc.slug = :category"
                count_params["category"] = category
            if search:
                count_query += " AND (t.name ILIKE :search OR t.tagline ILIKE :search)"
                count_params["search"] = f"%{search}%"

            total = conn.execute(text(count_query), count_params).scalar()

            twins = []
            for r in rows:
                twins.append({
                    "id": str(r[0]),
                    "name": r[1],
                    "slug": r[2],
                    "tagline": r[3],
                    "bio": r[4][:200] if r[4] else None,
                    "avatar_url": r[5],
                    "verification_level": r[6],
                    "total_chats": r[7],
                    "avg_fidelity": r[8],
                    "created_at": str(r[9]),
                    "category_name": r[10],
                })

            return {"twins": twins, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
