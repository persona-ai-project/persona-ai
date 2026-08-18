"""
routers/health.py
=================
Health check endpoints for monitoring.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Response
from sqlalchemy import create_engine, text

router = APIRouter(tags=["health"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/persona"
)

# Track startup time
STARTUP_TIME = datetime.now(timezone.utc)


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": (datetime.now(timezone.utc) - STARTUP_TIME).total_seconds(),
    }


@router.get("/health/ready")
async def readiness_check(response: Response):
    """
    Readiness check - verifies all dependencies are available.
    Returns 200 if ready, 503 if not.
    """
    checks = {}
    all_healthy = True
    
    # Check database
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False
    
    # Check Redis (if configured)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            checks["redis"] = {"status": "healthy"}
        except Exception as e:
            checks["redis"] = {"status": "unhealthy", "error": str(e)}
            # Redis is optional, don't fail health check
    
    # Check Qdrant (if configured)
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(url=qdrant_url)
            client.get_collections()
            checks["qdrant"] = {"status": "healthy"}
        except Exception as e:
            checks["qdrant"] = {"status": "unhealthy", "error": str(e)}
            # Qdrant is optional
    
    # Check LLM providers
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        checks["groq"] = {"status": "configured"}
    
    response.status_code = 200 if all_healthy else 503
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check - indicates the service is running.
    Used by orchestrators (K8s, Railway) to restart unhealthy instances.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/info")
async def service_info():
    """Service information endpoint."""
    return {
        "service": "persona-ai-api",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": {
            "twins": True,
            "voice": True,
            "enterprise_api": True,
            "analytics": True,
            "fidelity": True,
        },
        "limits": {
            "max_twins_per_user": 10,
            "max_sources_per_twin": 50,
            "max_message_length": 10000,
            "max_file_size_mb": 25,
        },
    }


@router.get("/metrics")
async def metrics():
    """
    Prometheus-compatible metrics endpoint.
    """
    # This is a simplified metrics endpoint
    # In production, use prometheus_client library
    return {
        "persona_api_requests_total": 0,  # Would be tracked in production
        "persona_api_latency_seconds": 0,
        "persona_api_errors_total": 0,
        "persona_twins_total": 0,
        "persona_users_total": 0,
    }
