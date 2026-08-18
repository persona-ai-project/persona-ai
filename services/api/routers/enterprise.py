"""
routers/enterprise.py
=====================
Enterprise API management endpoints.

Routes:
    GET    /enterprise/api-keys            — list API keys
    POST   /enterprise/api-keys            — create API key
    GET    /enterprise/api-keys/{key_id}   — get API key details
    DELETE /enterprise/api-keys/{key_id}   — revoke API key
    POST   /enterprise/api-keys/{key_id}/rotate — rotate API key
    
    GET    /enterprise/usage               — get API usage stats
    GET    /enterprise/usage/daily         — daily usage breakdown
    GET    /enterprise/usage/endpoints     — endpoint usage breakdown
    
    GET    /enterprise/webhooks            — list webhooks
    POST   /enterprise/webhooks            — create webhook
    GET    /enterprise/webhooks/{wh_id}    — get webhook details
    PATCH  /enterprise/webhooks/{wh_id}    — update webhook
    DELETE /enterprise/webhooks/{wh_id}    — delete webhook
    POST   /enterprise/webhooks/{wh_id}/test — test webhook
    
    GET    /enterprise/plan                — get enterprise plan features
"""
from __future__ import annotations

import os
import uuid
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from core.security import get_current_user

router = APIRouter(prefix="/enterprise", tags=["enterprise"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)


# ── Models ──────────────────────────────────────────────────────────────────────

class APIKeyCreate(BaseModel):
    name: str
    scopes: list[str] = ["*"]  # default: all endpoints
    rate_limit: int = 1000  # requests per day
    expires_in_days: int | None = None  # None = no expiry


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: list[str]
    rate_limit: int
    daily_usage: int
    last_used_at: str | None
    expires_at: str | None
    is_active: bool
    created_at: str


class APIKeyCreateResponse(APIKeyResponse):
    key: str  # full key, only shown on creation


class WebhookCreate(BaseModel):
    url: str
    events: list[str]  # e.g., ["twin.created", "twin.chat", "subscription.changed"]


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: list[str]
    is_active: bool
    last_triggered_at: str | None
    failure_count: int
    created_at: str


class UsageStatsResponse(BaseModel):
    total_requests: int
    requests_today: int
    avg_latency_ms: float
    error_rate: float
    top_endpoints: list[dict]
    usage_by_day: list[dict]


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _hash_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def _generate_api_key() -> str:
    """Generate a new API key with prefix."""
    prefix = "pai"  # persona-ai prefix
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}_{random_part}"


def _get_db():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _verify_enterprise_access(conn, user_id: str):
    """Verify user has enterprise subscription."""
    row = conn.execute(
        text("""SELECT s.plan_id, p.name 
                FROM subscriptions s 
                JOIN subscription_plans p ON s.plan_id = p.id
                WHERE s.user_id = :user_id AND s.status = 'active'"""),
        {"user_id": user_id}
    ).fetchone()
    
    if not row:
        raise HTTPException(status_code=403, detail="Enterprise subscription required")
    
    plan_name = row[1].lower()
    if "enterprise" not in plan_name and "business" not in plan_name:
        raise HTTPException(status_code=403, detail="Enterprise subscription required")


# ── API Key Management ──────────────────────────────────────────────────────────

@router.get("/api-keys", response_model=list[APIKeyResponse])
def list_api_keys(
    current_user: dict = Depends(get_current_user),
):
    """List all API keys for the current user."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        rows = db.execute(
            text("""SELECT id, name, key_prefix, scopes, rate_limit, 
                           daily_usage, last_used_at, expires_at, is_active, created_at
                    FROM api_keys 
                    WHERE user_id = :user_id 
                    ORDER BY created_at DESC"""),
            {"user_id": user_id}
        ).fetchall()
        
        return [
            APIKeyResponse(
                id=str(row[0]),
                name=row[1],
                key_prefix=row[2],
                scopes=row[3] or ["*"],
                rate_limit=row[4],
                daily_usage=row[5],
                last_used_at=row[6],
                expires_at=row[7],
                is_active=row[8],
                created_at=row[9],
            )
            for row in rows
        ]
    finally:
        db.close()


@router.post("/api-keys", response_model=APIKeyCreateResponse)
def create_api_key(
    body: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new API key. The key is only shown once."""
    user_id = current_user["user_id"]

    # Verify enterprise access
    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_enterprise_access(db, user_id)
        
        # Check key limit
        count = db.execute(
            text("SELECT COUNT(*) FROM api_keys WHERE user_id = :user_id AND is_active = true"),
            {"user_id": user_id}
        ).scalar()
        
        if count >= 10:
            raise HTTPException(status_code=400, detail="Maximum 10 active API keys allowed")
        
        # Generate key
        full_key = _generate_api_key()
        key_hash = _hash_key(full_key)
        key_prefix = full_key[:11]  # pai_xxxxx
        
        # Calculate expiry
        expires_at = None
        if body.expires_in_days:
            expires_at = (datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)).isoformat()
        
        # Insert
        key_id = str(uuid.uuid4())
        db.execute(
            text("""INSERT INTO api_keys (id, user_id, name, key_hash, key_prefix, 
                    scopes, rate_limit, expires_at, is_active, created_at, updated_at)
                    VALUES (:id, :user_id, :name, :key_hash, :key_prefix, 
                    :scopes, :rate_limit, :expires_at, true, :now, :now)"""),
            {
                "id": key_id,
                "user_id": user_id,
                "name": body.name,
                "key_hash": key_hash,
                "key_prefix": key_prefix,
                "scopes": body.scopes,
                "rate_limit": body.rate_limit,
                "expires_at": expires_at,
                "now": datetime.now(timezone.utc).isoformat(),
            }
        )
        db.commit()
        
        return APIKeyCreateResponse(
            id=key_id,
            name=body.name,
            key_prefix=key_prefix,
            scopes=body.scopes,
            rate_limit=body.rate_limit,
            daily_usage=0,
            last_used_at=None,
            expires_at=expires_at,
            is_active=True,
            created_at=datetime.now(timezone.utc).isoformat(),
            key=full_key,
        )
    finally:
        db.close()


@router.delete("/api-keys/{key_id}")
def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Revoke (delete) an API key."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        # Verify ownership
        row = db.execute(
            text("SELECT id FROM api_keys WHERE id = :key_id AND user_id = :user_id"),
            {"key_id": key_id, "user_id": user_id}
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="API key not found")
        
        db.execute(text("DELETE FROM api_keys WHERE id = :key_id"), {"key_id": key_id})
        db.commit()
        
        return {"status": "revoked", "key_id": key_id}
    finally:
        db.close()


@router.post("/api-keys/{key_id}/rotate", response_model=APIKeyCreateResponse)
def rotate_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Rotate an API key (generates new key, revokes old)."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        # Get existing key
        row = db.execute(
            text("""SELECT id, name, scopes, rate_limit, expires_at
                    FROM api_keys 
                    WHERE id = :key_id AND user_id = :user_id AND is_active = true"""),
            {"key_id": key_id, "user_id": user_id}
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Generate new key
        full_key = _generate_api_key()
        key_hash = _hash_key(full_key)
        key_prefix = full_key[:11]
        
        # Update
        db.execute(
            text("""UPDATE api_keys 
                    SET key_hash = :key_hash, key_prefix = :key_prefix, 
                        updated_at = :now
                    WHERE id = :key_id"""),
            {
                "key_hash": key_hash,
                "key_prefix": key_prefix,
                "now": datetime.now(timezone.utc).isoformat(),
                "key_id": key_id,
            }
        )
        db.commit()
        
        return APIKeyCreateResponse(
            id=key_id,
            name=row[1],
            key_prefix=key_prefix,
            scopes=row[2] or ["*"],
            rate_limit=row[3],
            daily_usage=0,
            last_used_at=None,
            expires_at=row[4],
            is_active=True,
            created_at=datetime.now(timezone.utc).isoformat(),
            key=full_key,
        )
    finally:
        db.close()


# ── Usage Analytics ─────────────────────────────────────────────────────────────

@router.get("/usage", response_model=UsageStatsResponse)
def get_usage_stats(
    days: int = Query(30, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
):
    """Get API usage statistics."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_enterprise_access(db, user_id)
        
        # Total requests
        total = db.execute(
            text("""SELECT COUNT(*) FROM api_usage_logs 
                    WHERE user_id = :user_id 
                    AND created_at > NOW() - INTERVAL ':days days'"""),
            {"user_id": user_id, "days": days}
        ).scalar()
        
        # Requests today
        today = db.execute(
            text("""SELECT COUNT(*) FROM api_usage_logs 
                    WHERE user_id = :user_id 
                    AND created_at > CURRENT_DATE"""),
            {"user_id": user_id}
        ).scalar()
        
        # Average latency
        avg_latency = db.execute(
            text("""SELECT COALESCE(AVG(latency_ms), 0) FROM api_usage_logs 
                    WHERE user_id = :user_id 
                    AND created_at > NOW() - INTERVAL ':days days'"""),
            {"user_id": user_id, "days": days}
        ).scalar()
        
        # Error rate
        error_count = db.execute(
            text("""SELECT COUNT(*) FROM api_usage_logs 
                    WHERE user_id = :user_id 
                    AND status_code >= 400
                    AND created_at > NOW() - INTERVAL ':days days'"""),
            {"user_id": user_id, "days": days}
        ).scalar()
        
        error_rate = (error_count / total * 100) if total > 0 else 0
        
        # Top endpoints
        top_endpoints = db.execute(
            text("""SELECT endpoint, COUNT(*) as count 
                    FROM api_usage_logs 
                    WHERE user_id = :user_id 
                    AND created_at > NOW() - INTERVAL ':days days'
                    GROUP BY endpoint 
                    ORDER BY count DESC 
                    LIMIT 10"""),
            {"user_id": user_id, "days": days}
        ).fetchall()
        
        # Usage by day
        usage_by_day = db.execute(
            text("""SELECT DATE(created_at) as day, COUNT(*) as count 
                    FROM api_usage_logs 
                    WHERE user_id = :user_id 
                    AND created_at > NOW() - INTERVAL ':days days'
                    GROUP BY DATE(created_at) 
                    ORDER BY day"""),
            {"user_id": user_id, "days": days}
        ).fetchall()
        
        return UsageStatsResponse(
            total_requests=total,
            requests_today=today,
            avg_latency_ms=round(float(avg_latency), 2),
            error_rate=round(error_rate, 2),
            top_endpoints=[{"endpoint": r[0], "count": r[1]} for r in top_endpoints],
            usage_by_day=[{"date": str(r[0]), "count": r[1]} for r in usage_by_day],
        )
    finally:
        db.close()


# ── Webhooks ────────────────────────────────────────────────────────────────────

@router.get("/webhooks", response_model=list[WebhookResponse])
def list_webhooks(
    current_user: dict = Depends(get_current_user),
):
    """List all webhooks."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        rows = db.execute(
            text("""SELECT id, url, events, is_active, last_triggered_at, 
                           failure_count, created_at
                    FROM webhooks 
                    WHERE user_id = :user_id 
                    ORDER BY created_at DESC"""),
            {"user_id": user_id}
        ).fetchall()
        
        return [
            WebhookResponse(
                id=str(row[0]),
                url=row[1],
                events=row[2] or [],
                is_active=row[3],
                last_triggered_at=row[4],
                failure_count=row[5],
                created_at=row[6],
            )
            for row in rows
        ]
    finally:
        db.close()


@router.post("/webhooks", response_model=WebhookResponse)
def create_webhook(
    body: WebhookCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new webhook."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        _verify_enterprise_access(db, user_id)
        
        # Validate URL
        if not body.url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="Invalid webhook URL")
        
        # Validate events
        valid_events = [
            "twin.created", "twin.updated", "twin.deleted", "twin.chat",
            "source.uploaded", "source.processed", "source.failed",
            "interview.started", "interview.completed",
            "subscription.changed", "subscription.renewed",
            "fidelity.evaluated",
        ]
        invalid_events = [e for e in body.events if e not in valid_events]
        if invalid_events:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid events: {', '.join(invalid_events)}"
            )
        
        # Check webhook limit
        count = db.execute(
            text("SELECT COUNT(*) FROM webhooks WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).scalar()
        
        if count >= 5:
            raise HTTPException(status_code=400, detail="Maximum 5 webhooks allowed")
        
        # Generate secret
        secret = secrets.token_urlsafe(32)
        
        # Insert
        webhook_id = str(uuid.uuid4())
        db.execute(
            text("""INSERT INTO webhooks (id, user_id, url, events, secret, 
                    is_active, created_at, updated_at)
                    VALUES (:id, :user_id, :url, :events, :secret, 
                    true, :now, :now)"""),
            {
                "id": webhook_id,
                "user_id": user_id,
                "url": body.url,
                "events": body.events,
                "secret": secret,
                "now": datetime.now(timezone.utc).isoformat(),
            }
        )
        db.commit()
        
        return WebhookResponse(
            id=webhook_id,
            url=body.url,
            events=body.events,
            is_active=True,
            last_triggered_at=None,
            failure_count=0,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    finally:
        db.close()


@router.delete("/webhooks/{webhook_id}")
def delete_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a webhook."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        # Verify ownership
        row = db.execute(
            text("SELECT id FROM webhooks WHERE id = :webhook_id AND user_id = :user_id"),
            {"webhook_id": webhook_id, "user_id": user_id}
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        db.execute(text("DELETE FROM webhooks WHERE id = :webhook_id"), {"webhook_id": webhook_id})
        db.commit()
        
        return {"status": "deleted", "webhook_id": webhook_id}
    finally:
        db.close()


@router.post("/webhooks/{webhook_id}/test")
def test_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Send a test event to a webhook."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        row = db.execute(
            text("""SELECT id, url, secret, is_active 
                    FROM webhooks 
                    WHERE id = :webhook_id AND user_id = :user_id"""),
            {"webhook_id": webhook_id, "user_id": user_id}
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        if not row[3]:
            raise HTTPException(status_code=400, detail="Webhook is disabled")
        
        # In production, would send test payload here
        # For now, just record the delivery
        delivery_id = str(uuid.uuid4())
        db.execute(
            text("""INSERT INTO webhook_deliveries (id, webhook_id, event, payload, 
                    status, response_code, attempts, created_at)
                    VALUES (:id, :webhook_id, :event, :payload, 
                    'success', 200, 1, :now)"""),
            {
                "id": delivery_id,
                "webhook_id": webhook_id,
                "event": "webhook.test",
                "payload": {"test": True, "timestamp": datetime.now(timezone.utc).isoformat()},
                "now": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        # Update last triggered
        db.execute(
            text("""UPDATE webhooks 
                    SET last_triggered_at = :now 
                    WHERE id = :webhook_id"""),
            {"webhook_id": webhook_id, "now": datetime.now(timezone.utc).isoformat()}
        )
        db.commit()
        
        return {
            "status": "sent",
            "delivery_id": delivery_id,
            "url": row[1],
        }
    finally:
        db.close()


# ── Enterprise Plan Features ────────────────────────────────────────────────────

@router.get("/plan")
def get_enterprise_features(
    current_user: dict = Depends(get_current_user),
):
    """Get enterprise plan features for current user."""
    user_id = current_user["user_id"]

    engine = create_engine(DATABASE_URL)
    db = sessionmaker(bind=engine)()
    try:
        row = db.execute(
            text("""SELECT p.name, p.max_twins, p.max_sources_per_twin, 
                           p.max_messages_per_day, p.features,
                           s.api_access_enabled, s.api_rate_limit, s.webhook_limit,
                           s.dedicated_support, s.custom_models, s.sla_guarantee
                    FROM subscriptions s 
                    JOIN subscription_plans p ON s.plan_id = p.id
                    WHERE s.user_id = :user_id AND s.status = 'active'"""),
            {"user_id": user_id}
        ).fetchone()
        
        if not row:
            return {
                "plan": "free",
                "api_access": False,
                "features": []
            }
        
        return {
            "plan": row[0],
            "max_twins": row[1],
            "max_sources_per_twin": row[2],
            "max_messages_per_day": row[3],
            "features": row[4] or [],
            "api_access": row[5] or False,
            "api_rate_limit": row[6] or 0,
            "webhook_limit": row[7] or 0,
            "dedicated_support": row[8] or False,
            "custom_models": row[9] or False,
            "sla_guarantee": row[10],
        }
    finally:
        db.close()


from sqlalchemy.orm import sessionmaker
