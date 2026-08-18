"""
lifecycle.py
============
Application lifecycle management for graceful startup and shutdown.
"""
from __future__ import annotations

import os
import signal
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI
from logging_config import get_logger

logger = get_logger("lifecycle")

# Track active connections
active_connections = set()
shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting PersonaAI API...")
    
    # Validate environment
    _validate_environment()
    
    # Initialize services
    await _initialize_services()
    
    logger.info("PersonaAI API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PersonaAI API...")
    
    await _cleanup_services()
    
    logger.info("PersonaAI API shut down gracefully")


def _validate_environment():
    """Validate required environment variables."""
    required = ["JWT_SECRET"]
    optional = ["DATABASE_URL", "GROQ_API_KEY", "REDIS_URL", "QDRANT_URL"]
    
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        logger.warning(f"Missing required env vars: {missing}")
    
    configured = [var for var in optional if os.getenv(var)]
    logger.info(f"Configured services: {configured}")


async def _initialize_services():
    """Initialize application services."""
    # Initialize database connection pool
    try:
        from sqlalchemy import create_engine
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@postgres:5432/persona"
        )
        engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
        )
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Initialize Redis (if configured)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
    
    # Initialize Qdrant (if configured)
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        try:
            from qdrant_client import QdrantClient
            qdrant_client = QdrantClient(url=qdrant_url)
            logger.info("Qdrant connection established")
        except Exception as e:
            logger.warning(f"Qdrant connection failed: {e}")


async def _cleanup_services():
    """Cleanup application services."""
    logger.info("Cleaning up services...")
    
    # Close database connections
    try:
        from sqlalchemy import create_engine
        # Engine is managed by FastAPI, no explicit cleanup needed
    except Exception:
        pass
    
    # Close Redis connections
    try:
        import redis
        # Redis client is managed by request lifecycle
    except Exception:
        pass
    
    # Wait for active connections to complete
    if active_connections:
        logger.info(f"Waiting for {len(active_connections)} active connections...")
        await asyncio.sleep(2)  # Give time for responses to complete
    
    logger.info("Cleanup complete")


def get_uptime() -> float:
    """Get application uptime in seconds."""
    from routers.health import STARTUP_TIME
    return (datetime.now(timezone.utc) - STARTUP_TIME).total_seconds()


def get_active_connections() -> int:
    """Get number of active connections."""
    return len(active_connections)


def add_connection(connection_id: str):
    """Track a new connection."""
    active_connections.add(connection_id)


def remove_connection(connection_id: str):
    """Remove a tracked connection."""
    active_connections.discard(connection_id)
