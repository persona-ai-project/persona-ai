"""
routers/analytics.py
====================
Analytics and insights API endpoints.

Routes:
    GET /analytics/overview           — overall platform stats
    GET /analytics/twins/{twin_id}    — twin-specific analytics
    GET /analytics/engagement         — engagement metrics
    GET /analytics/knowledge          — knowledge base analytics
    GET /analytics/trends             — trend data over time
"""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from core.security import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)


# ── Models ──────────────────────────────────────────────────────────────────────

class OverviewResponse(BaseModel):
    total_users: int
    total_twins: int
    total_chats: int
    total_messages: int
    total_sources: int
    total_knowledge_items: int
    active_twins: int
    public_twins: int
    avg_fidelity: float | None


class TwinAnalytics(BaseModel):
    twin_id: str
    name: str
    total_chats: int
    total_messages: int
    avg_fidelity: float | None
    knowledge_count: int
    source_count: int
    interview_count: int
    access_count: int
    unique_visitors: int
    top_knowledge_types: dict
    chat_history: list[dict]
    daily_activity: list[dict]


class EngagementMetrics(BaseModel):
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    avg_session_duration: float | None
    avg_messages_per_session: float
    retention_rate: float | None
    peak_hours: list[dict]


class KnowledgeAnalytics(BaseModel):
    total_items: int
    by_type: dict
    by_source: dict
    avg_confidence: float
    coverage_score: float
    quality_score: float


class TrendData(BaseModel):
    period: str
    data: list[dict]


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _get_db():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.get("/overview", response_model=OverviewResponse)
def get_overview():
    """Get overall platform analytics."""
    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        # Total users
        total_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar()

        # Total twins
        total_twins = db.execute(text("SELECT COUNT(*) FROM twins WHERE is_active = true")).scalar()

        # Total chats
        total_chats = db.execute(
            text("SELECT COALESCE(SUM(total_chats), 0) FROM twins")
        ).scalar()

        # Total messages
        total_messages = db.execute(
            text("SELECT COALESCE(SUM(total_messages), 0) FROM twins")
        ).scalar()

        # Total sources
        total_sources = db.execute(
            text("SELECT COUNT(*) FROM sources")
        ).scalar()

        # Total knowledge items
        total_knowledge = db.execute(
            text("SELECT COUNT(*) FROM knowledge_items WHERE is_active = true")
        ).scalar()

        # Active twins (chatted in last 7 days)
        active_twins = db.execute(
            text("""SELECT COUNT(DISTINCT persona_id) FROM messages 
                    WHERE created_at >= NOW() - INTERVAL '7 days' AND persona_id IS NOT NULL""")
        ).scalar()

        # Public twins
        public_twins = db.execute(
            text("SELECT COUNT(*) FROM twins WHERE visibility = 'public' AND is_active = true")
        ).scalar()

        # Average fidelity
        avg_fidelity = db.execute(
            text("SELECT AVG(avg_fidelity) FROM twins WHERE avg_fidelity IS NOT NULL")
        ).scalar()

        return OverviewResponse(
            total_users=total_users or 0,
            total_twins=total_twins or 0,
            total_chats=total_chats or 0,
            total_messages=total_messages or 0,
            total_sources=total_sources or 0,
            total_knowledge_items=total_knowledge or 0,
            active_twins=active_twins or 0,
            public_twins=public_twins or 0,
            avg_fidelity=round(avg_fidelity, 3) if avg_fidelity else None,
        )
    finally:
        db.close()


@router.get("/twins/{twin_id}", response_model=TwinAnalytics)
def get_twin_analytics(
    twin_id: str,
    current_user: dict = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365),
):
    """Get detailed analytics for a specific twin."""
    user_id = current_user["id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_twin_owner(db, twin_id, user_id)

        # Twin basic info
        twin = db.execute(
            text("""SELECT name, total_chats, total_messages, avg_fidelity
                    FROM twins WHERE id = :id"""),
            {"id": twin_id}
        ).fetchone()

        # Knowledge count
        knowledge_count = db.execute(
            text("""SELECT COUNT(*) FROM knowledge_items 
                    WHERE twin_id = :tid AND is_active = true"""),
            {"tid": twin_id}
        ).scalar()

        # Source count
        source_count = db.execute(
            text("SELECT COUNT(*) FROM sources WHERE twin_id = :tid"),
            {"tid": twin_id}
        ).scalar()

        # Interview count
        interview_count = db.execute(
            text("SELECT COUNT(*) FROM interview_sessions WHERE twin_id = :tid"),
            {"tid": twin_id}
        ).scalar()

        # Access count
        access_count = db.execute(
            text("SELECT COUNT(*) FROM twin_access_logs WHERE twin_id = :tid"),
            {"tid": twin_id}
        ).scalar()

        # Unique visitors
        unique_visitors = db.execute(
            text("SELECT COUNT(DISTINCT user_id) FROM twin_access_logs WHERE twin_id = :tid AND user_id IS NOT NULL"),
            {"tid": twin_id}
        ).scalar()

        # Top knowledge types
        knowledge_types = db.execute(
            text("""SELECT content_type, COUNT(*) as count
                    FROM knowledge_items 
                    WHERE twin_id = :tid AND is_active = true
                    GROUP BY content_type
                    ORDER BY count DESC"""),
            {"tid": twin_id}
        ).fetchall()

        # Chat history (last N days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        chat_history = db.execute(
            text("""SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM messages 
                    WHERE persona_id = :tid AND role = 'assistant' AND created_at >= :cutoff
                    GROUP BY DATE(created_at)
                    ORDER BY date"""),
            {"tid": twin_id, "cutoff": cutoff}
        ).fetchall()

        # Daily activity
        daily_activity = db.execute(
            text("""SELECT DATE(created_at) as date, 
                           COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
                           COUNT(CASE WHEN role = 'assistant' THEN 1 END) as assistant_messages
                    FROM messages 
                    WHERE persona_id = :tid AND created_at >= :cutoff
                    GROUP BY DATE(created_at)
                    ORDER BY date"""),
            {"tid": twin_id, "cutoff": cutoff}
        ).fetchall()

        return TwinAnalytics(
            twin_id=twin_id,
            name=twin[0] if twin else "Unknown",
            total_chats=twin[1] if twin else 0,
            total_messages=twin[2] if twin else 0,
            avg_fidelity=twin[3] if twin else None,
            knowledge_count=knowledge_count or 0,
            source_count=source_count or 0,
            interview_count=interview_count or 0,
            access_count=access_count or 0,
            unique_visitors=unique_visitors or 0,
            top_knowledge_types={r[0]: r[1] for r in knowledge_types},
            chat_history=[{"date": str(r[0]), "count": r[1]} for r in chat_history],
            daily_activity=[
                {"date": str(r[0]), "user_messages": r[1], "assistant_messages": r[2]}
                for r in daily_activity
            ],
        )
    finally:
        db.close()


@router.get("/engagement", response_model=EngagementMetrics)
def get_engagement_metrics(current_user: dict = Depends(get_current_user)):
    """Get engagement metrics for the platform."""
    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        now = datetime.now(timezone.utc)

        # Daily active users
        dau = db.execute(
            text("""SELECT COUNT(DISTINCT user_id) FROM messages 
                    WHERE created_at >= CURRENT_DATE""")
        ).scalar()

        # Weekly active users
        wau = db.execute(
            text("""SELECT COUNT(DISTINCT user_id) FROM messages 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'""")
        ).scalar()

        # Monthly active users
        mau = db.execute(
            text("""SELECT COUNT(DISTINCT user_id) FROM messages 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'""")
        ).scalar()

        # Average messages per session (approximate by day)
        avg_messages = db.execute(
            text("""SELECT AVG(daily_count) FROM (
                    SELECT user_id, DATE(created_at), COUNT(*) as daily_count
                    FROM messages
                    GROUP BY user_id, DATE(created_at)
                ) subquery""")
        ).scalar()

        # Peak hours
        peak_hours = db.execute(
            text("""SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as count
                    FROM messages 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY EXTRACT(HOUR FROM created_at)
                    ORDER BY count DESC
                    LIMIT 5""")
        ).fetchall()

        return EngagementMetrics(
            daily_active_users=dau or 0,
            weekly_active_users=wau or 0,
            monthly_active_users=mau or 0,
            avg_session_duration=None,  # Would need session tracking
            avg_messages_per_session=round(avg_messages or 0, 1),
            retention_rate=None,  # Would need cohort analysis
            peak_hours=[{"hour": int(r[0]), "count": r[1]} for r in peak_hours],
        )
    finally:
        db.close()


@router.get("/knowledge", response_model=KnowledgeAnalytics)
def get_knowledge_analytics(
    twin_id: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    """Get knowledge base analytics."""
    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        user_id = current_user["id"]

        # Build query based on twin_id
        if twin_id:
            _verify_twin_owner(db, twin_id, user_id)
            where_clause = "WHERE ki.twin_id = :tid AND ki.is_active = true"
            params = {"tid": twin_id}
        else:
            where_clause = """WHERE ki.twin_id IN (
                SELECT id FROM twins WHERE owner_id = :uid AND is_active = true
            ) AND ki.is_active = true"""
            params = {"uid": user_id}

        # Total items
        total = db.execute(
            text(f"SELECT COUNT(*) FROM knowledge_items ki {where_clause}"),
            params
        ).scalar()

        # By type
        by_type = db.execute(
            text(f"""SELECT content_type, COUNT(*) as count
                    FROM knowledge_items ki {where_clause}
                    GROUP BY content_type
                    ORDER BY count DESC"""),
            params
        ).fetchall()

        # By source
        by_source = db.execute(
            text(f"""SELECT s.source_type, COUNT(*) as count
                    FROM knowledge_items ki
                    LEFT JOIN sources s ON ki.source_id = s.id
                    {where_clause.replace('ki.', 'ki.')}
                    GROUP BY s.source_type
                    ORDER BY count DESC"""),
            params
        ).fetchall()

        # Average confidence
        avg_confidence = db.execute(
            text(f"SELECT AVG(confidence) FROM knowledge_items ki {where_clause}"),
            params
        ).scalar()

        # Coverage score (based on knowledge types present)
        coverage = db.execute(
            text(f"""SELECT COUNT(DISTINCT content_type) FROM knowledge_items ki {where_clause}"""),
            params
        ).scalar()

        # Quality score (average confidence * coverage)
        quality = (avg_confidence or 0) * (coverage or 0) / 7  # 7 possible types

        return KnowledgeAnalytics(
            total_items=total or 0,
            by_type={r[0]: r[1] for r in by_type},
            by_source={r[0] or "unknown": r[1] for r in by_source},
            avg_confidence=round(avg_confidence or 0, 3),
            coverage_score=round((coverage or 0) / 7, 3),
            quality_score=round(quality, 3),
        )
    finally:
        db.close()


@router.get("/trends")
def get_trends(
    metric: str = "chats",
    period: str = "daily",
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Get trend data over time."""
    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        user_id = current_user["id"]
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Determine date truncation
        trunc = "day" if period == "daily" else "week" if period == "weekly" else "month"

        # Get twins owned by user
        twins = db.execute(
            text("SELECT id FROM twins WHERE owner_id = :uid AND is_active = true"),
            {"uid": user_id}
        ).fetchall()
        twin_ids = [str(t[0]) for t in twins]

        if not twin_ids:
            return {"period": period, "data": []}

        if metric == "chats":
            data = db.execute(
                text(f"""SELECT DATE_TRUNC('{trunc}', created_at) as date, COUNT(*) as count
                        FROM messages 
                        WHERE persona_id = ANY(:tids) AND role = 'assistant' AND created_at >= :cutoff
                        GROUP BY DATE_TRUNC('{trunc}', created_at)
                        ORDER BY date"""),
                {"tids": twin_ids, "cutoff": cutoff}
            ).fetchall()
        elif metric == "messages":
            data = db.execute(
                text(f"""SELECT DATE_TRUNC('{trunc}', created_at) as date, COUNT(*) as count
                        FROM messages 
                        WHERE persona_id = ANY(:tids) AND created_at >= :cutoff
                        GROUP BY DATE_TRUNC('{trunc}', created_at)
                        ORDER BY date"""),
                {"tids": twin_ids, "cutoff": cutoff}
            ).fetchall()
        elif metric == "knowledge":
            data = db.execute(
                text(f"""SELECT DATE_TRUNC('{trunc}', created_at) as date, COUNT(*) as count
                        FROM knowledge_items 
                        WHERE twin_id = ANY(:tids) AND created_at >= :cutoff
                        GROUP BY DATE_TRUNC('{trunc}', created_at)
                        ORDER BY date"""),
                {"tids": twin_ids, "cutoff": cutoff}
            ).fetchall()
        elif metric == "sources":
            data = db.execute(
                text(f"""SELECT DATE_TRUNC('{trunc}', created_at) as date, COUNT(*) as count
                        FROM sources 
                        WHERE twin_id = ANY(:tids) AND created_at >= :cutoff
                        GROUP BY DATE_TRUNC('{trunc}', created_at)
                        ORDER BY date"""),
                {"tids": twin_ids, "cutoff": cutoff}
            ).fetchall()
        else:
            return {"period": period, "data": []}

        return {
            "period": period,
            "data": [{"date": str(r[0]), "count": r[1]} for r in data],
        }
    finally:
        db.close()


from sqlalchemy.orm import sessionmaker
