"""
middleware/api_key_auth.py
=========================
API key authentication middleware for enterprise access.

Validates API keys, checks rate limits, and logs usage.
"""
from __future__ import annotations

import os
import hashlib
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)


def _hash_key(key: str) -> str:
    """Hash an API key for comparison."""
    return hashlib.sha256(key.encode()).hexdigest()


async def validate_api_key(request: Request) -> Optional[dict]:
    """
    Validate API key from request.
    
    Checks:
    1. Key exists and is active
    2. Key hasn't expired
    3. Rate limit not exceeded
    4. Endpoint is allowed by scopes
    
    Returns user info if valid, None if no API key (use JWT auth instead).
    """
    # Get API key from header
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None  # No API key, use JWT auth
    
    # Hash the key
    key_hash = _hash_key(api_key)
    
    engine = create_engine(DATABASE_URL)
    db = engine.connect()
    try:
        # Look up key
        row = db.execute(
            text("""SELECT id, user_id, key_prefix, scopes, rate_limit, 
                           daily_usage, expires_at, is_active
                    FROM api_keys 
                    WHERE key_hash = :key_hash"""),
            {"key_hash": key_hash}
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        if not row[7]:  # is_active
            raise HTTPException(status_code=401, detail="API key has been revoked")
        
        # Check expiry
        if row[6]:  # expires_at
            expires_at = datetime.fromisoformat(row[6].replace("Z", "+00:00"))
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=401, detail="API key has expired")
        
        # Check rate limit
        # Reset daily usage if needed (simple daily reset)
        today = datetime.now(timezone.utc).date().isoformat()
        last_reset = db.execute(
            text("""SELECT DATE(created_at) FROM api_usage_logs 
                    WHERE api_key_id = :key_id 
                    ORDER BY created_at DESC LIMIT 1"""),
            {"key_id": row[0]}
        ).scalar()
        
        if last_reset and str(last_reset) < today:
            # Reset daily usage
            db.execute(
                text("""UPDATE api_keys 
                        SET daily_usage = 0 
                        WHERE id = :key_id"""),
                {"key_id": row[0]}
            )
            db.commit()
            current_usage = 0
        else:
            current_usage = row[5]
        
        if current_usage >= row[4]:  # daily_usage >= rate_limit
            raise HTTPException(
                status_code=429, 
                detail="API rate limit exceeded. Please try again tomorrow."
            )
        
        # Check endpoint scope
        endpoint = request.url.path
        scopes = row[3] or ["*"]
        
        if "*" not in scopes:
            # Check if endpoint matches any scope
            allowed = False
            for scope in scopes:
                if endpoint.startswith(scope):
                    allowed = True
                    break
            
            if not allowed:
                raise HTTPException(
                    status_code=403,
                    detail=f"API key does not have access to {endpoint}"
                )
        
        # Increment usage
        db.execute(
            text("""UPDATE api_keys 
                    SET daily_usage = daily_usage + 1, 
                        last_used_at = :now
                    WHERE id = :key_id"""),
            {"key_id": row[0], "now": datetime.now(timezone.utc).isoformat()}
        )
        db.commit()
        
        # Log usage
        log_id = f"{row[0]}_{int(time.time() * 1000)}"
        db.execute(
            text("""INSERT INTO api_usage_logs 
                    (id, api_key_id, user_id, endpoint, method, status_code, 
                     ip_address, user_agent, created_at)
                    VALUES (:id, :api_key_id, :user_id, :endpoint, :method, 
                     0, :ip, :ua, :now)"""),
            {
                "id": log_id,
                "api_key_id": row[0],
                "user_id": row[1],
                "endpoint": endpoint,
                "method": request.method,
                "ip": request.client.host if request.client else None,
                "ua": request.headers.get("user-agent"),
                "now": datetime.now(timezone.utc).isoformat(),
            }
        )
        db.commit()
        
        return {
            "user_id": row[1],
            "api_key_id": row[0],
            "key_prefix": row[2],
        }
    finally:
        db.close()


def update_usage_status(log_id: str, status_code: int, latency_ms: int, response_size: int):
    """Update API usage log with response details."""
    engine = create_engine(DATABASE_URL)
    db = engine.connect()
    try:
        db.execute(
            text("""UPDATE api_usage_logs 
                    SET status_code = :status_code, 
                        latency_ms = :latency_ms,
                        response_size = :response_size
                    WHERE id = :log_id"""),
            {
                "log_id": log_id,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "response_size": response_size,
            }
        )
        db.commit()
    finally:
        db.close()
