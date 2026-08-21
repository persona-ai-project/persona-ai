"""
routers/subscriptions.py
========================
Subscription management API endpoints.

Routes:
    GET  /subscriptions/plans              — list all plans (public)
    GET  /subscriptions/me                 — get current subscription
    GET  /subscriptions/me/usage           — get usage stats
    POST /subscriptions/change             — change plan (mock)
    GET  /subscriptions/me/history         — billing history (placeholder)
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from core.security import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)


# ── Models ──────────────────────────────────────────────────────────────────────

class PlanResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str | None
    max_twins: int
    max_sources_per_twin: int
    max_messages_per_day: int
    max_interview_sessions: int
    features: list[str] | None
    price_monthly: int | None
    price_yearly: int | None


class SubscriptionResponse(BaseModel):
    id: str
    plan: PlanResponse
    status: str
    current_period_start: str | None
    current_period_end: str | None
    created_at: str


class UsageResponse(BaseModel):
    twins_used: int
    twins_limit: int
    sources_used: int
    sources_limit: int
    messages_today: int
    messages_limit: int
    interviews_used: int
    interviews_limit: int


class ChangePlanRequest(BaseModel):
    plan_name: str  # "free", "pro", "enterprise"


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _get_db():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Routes ──────────────────────────────────────────────────────────────────────

@router.get("/plans", response_model=list[PlanResponse])
def list_plans():
    """List all available subscription plans (public)."""
    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        rows = db.execute(
            text("""SELECT id, name, display_name, description,
                           max_twins, max_sources_per_twin, max_messages_per_day,
                           max_interview_sessions, features, price_monthly, price_yearly
                    FROM subscription_plans
                    WHERE is_active = true
                    ORDER BY price_monthly ASC NULLS FIRST""")
        ).fetchall()

        return [
            PlanResponse(
                id=str(r[0]),
                name=r[1],
                display_name=r[2],
                description=r[3],
                max_twins=r[4],
                max_sources_per_twin=r[5],
                max_messages_per_day=r[6],
                max_interview_sessions=r[7],
                features=r[8] if isinstance(r[8], list) else (r[8].split(",") if r[8] else []),
                price_monthly=r[9],
                price_yearly=r[10],
            )
            for r in rows
        ]
    finally:
        db.close()


@router.get("/me", response_model=SubscriptionResponse)
def get_my_subscription(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        row = db.execute(
            text("""SELECT us.id, us.status, us.current_period_start, us.current_period_end,
                           us.created_at,
                           sp.id, sp.name, sp.display_name, sp.description,
                           sp.max_twins, sp.max_sources_per_twin, sp.max_messages_per_day,
                           sp.max_interview_sessions, sp.features, sp.price_monthly, sp.price_yearly
                    FROM user_subscriptions us
                    JOIN subscription_plans sp ON us.plan_id = sp.id
                    WHERE us.user_id = :uid AND us.status = 'active'
                    ORDER BY us.created_at DESC LIMIT 1"""),
            {"uid": user_id}
        ).fetchone()

        if not row:
            # Auto-create free subscription
            free_plan = db.execute(
                text("SELECT id FROM subscription_plans WHERE name = 'free'")
            ).fetchone()

            if free_plan:
                sub_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc)
                db.execute(
                    text("""INSERT INTO user_subscriptions 
                        (id, user_id, plan_id, status, current_period_start, current_period_end, twins_used, messages_today, created_at, updated_at)
                        VALUES (:id, :uid, :pid, 'active', :now, :end, 0, 0, :created, :now)"""),
                    {
                        "id": sub_id,
                        "uid": user_id,
                        "pid": str(free_plan[0]),
                        "now": now,
                        "end": now.replace(year=now.year + 1),
                        "created": now,
                    }
                )
                db.commit()

                # Re-fetch
                row = db.execute(
                    text("""SELECT us.id, us.status, us.current_period_start, us.current_period_end,
                                   us.created_at,
                                   sp.id, sp.name, sp.display_name, sp.description,
                                   sp.max_twins, sp.max_sources_per_twin, sp.max_messages_per_day,
                                   sp.max_interview_sessions, sp.features, sp.price_monthly, sp.price_yearly
                            FROM user_subscriptions us
                            JOIN subscription_plans sp ON us.plan_id = sp.id
                            WHERE us.id = :sid"""),
                    {"sid": sub_id}
                ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="No subscription found")

        return SubscriptionResponse(
            id=str(row[0]),
            plan=PlanResponse(
                id=str(row[5]),
                name=row[6],
                display_name=row[7],
                description=row[8],
                max_twins=row[9],
                max_sources_per_twin=row[10],
                max_messages_per_day=row[11],
                max_interview_sessions=row[12],
                features=row[13] if isinstance(row[13], list) else (row[13].split(",") if row[13] else []),
                price_monthly=row[14],
                price_yearly=row[15],
            ),
            status=row[1],
            current_period_start=str(row[2]) if row[2] else None,
            current_period_end=str(row[3]) if row[3] else None,
            created_at=str(row[4]),
        )
    finally:
        db.close()


@router.get("/me/usage", response_model=UsageResponse)
def get_my_usage(current_user: dict = Depends(get_current_user)):
    """Get current user's usage stats."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        # Get subscription limits
        sub = db.execute(
            text("""SELECT sp.max_twins, sp.max_sources_per_twin, sp.max_messages_per_day,
                           sp.max_interview_sessions
                    FROM user_subscriptions us
                    JOIN subscription_plans sp ON us.plan_id = sp.id
                    WHERE us.user_id = :uid AND us.status = 'active'"""),
            {"uid": user_id}
        ).fetchone()

        if not sub:
            return UsageResponse(
                twins_used=0, twins_limit=1,
                sources_used=0, sources_limit=5,
                messages_today=0, messages_limit=100,
                interviews_used=0, interviews_limit=3,
            )

        # Count twins
        twins_used = db.execute(
            text("SELECT COUNT(*) FROM twins WHERE owner_id = :uid AND is_active = true"),
            {"uid": user_id}
        ).scalar()

        # Count sources across all twins
        sources_used = db.execute(
            text("""SELECT COUNT(*) FROM sources 
                    WHERE twin_id IN (SELECT id FROM twins WHERE owner_id = :uid)"""),
            {"uid": user_id}
        ).scalar()

        # Count messages today
        messages_today = db.execute(
            text("""SELECT COUNT(*) FROM messages 
                    WHERE user_id = :uid AND created_at >= CURRENT_DATE"""),
            {"uid": user_id}
        ).scalar()

        # Count interviews
        interviews_used = db.execute(
            text("""SELECT COUNT(*) FROM interview_sessions 
                    WHERE user_id = :uid"""),
            {"uid": user_id}
        ).scalar()

        return UsageResponse(
            twins_used=twins_used,
            twins_limit=sub[0],
            sources_used=sources_used,
            sources_limit=sub[1],
            messages_today=messages_today,
            messages_limit=sub[2],
            interviews_used=interviews_used,
            interviews_limit=sub[3],
        )
    finally:
        db.close()


@router.post("/change")
def change_plan(body: ChangePlanRequest, current_user: dict = Depends(get_current_user)):
    """Change subscription plan (mock implementation)."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        # Get target plan
        plan = db.execute(
            text("SELECT id, name FROM subscription_plans WHERE name = :name AND is_active = true"),
            {"name": body.plan_name}
        ).fetchone()

        if not plan:
            raise HTTPException(status_code=400, detail="Invalid plan name")

        # Get current subscription
        current = db.execute(
            text("""SELECT id, plan_id FROM user_subscriptions 
                    WHERE user_id = :uid AND status = 'active'"""),
            {"uid": user_id}
        ).fetchone()

        if current and str(current[1]) == str(plan[0]):
            raise HTTPException(status_code=400, detail="Already on this plan")

        # Update or create subscription
        now = datetime.now(timezone.utc)
        if current:
            db.execute(
                text("""UPDATE user_subscriptions 
                       SET plan_id = :plan_id, updated_at = :now
                       WHERE id = :id"""),
                {"plan_id": str(plan[0]), "now": now, "id": str(current[0])}
            )
        else:
            db.execute(
                text("""INSERT INTO user_subscriptions 
                    (id, user_id, plan_id, status, current_period_start, current_period_end, twins_used, messages_today, created_at, updated_at)
                    VALUES (:id, :uid, :pid, 'active', :now, :end, 0, 0, :created, :now)"""),
                {
                    "id": str(uuid.uuid4()),
                    "uid": user_id,
                    "pid": str(plan[0]),
                    "now": now,
                    "end": now.replace(year=now.year + 1),
                    "created": now,
                }
            )

        db.commit()

        return {
            "message": f"Plan changed to {body.plan_name}",
            "plan": body.plan_name,
            "note": "This is a mock implementation. In production, this would integrate with Stripe."
        }
    finally:
        db.close()


@router.get("/me/history")
def get_billing_history(current_user: dict = Depends(get_current_user)):
    """Get billing history (placeholder)."""
    return {
        "history": [],
        "note": "Billing history will be available when payment integration is complete."
    }


from sqlalchemy.orm import sessionmaker
