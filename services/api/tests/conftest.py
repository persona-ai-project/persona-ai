"""
conftest.py
===========
Pytest fixtures for testing.
"""
import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI app."""
    # Set test environment variables
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
    os.environ["JWT_SECRET"] = "test-secret-key"
    os.environ["JWT_ALGORITHM"] = "HS256"
    
    # Import after setting env vars
    from main import app
    client = TestClient(app)
    yield client


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    db.execute.return_value = MagicMock()
    db.commit.return_value = None
    db.close.return_value = None
    return db


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {
        "user_id": "test-user-id-123",
        "email": "test@example.com",
    }


@pytest.fixture
def mock_twin():
    """Mock twin data."""
    return {
        "id": "twin-123",
        "name": "Test Twin",
        "slug": "test-twin",
        "owner_id": "test-user-id-123",
        "tagline": "A test twin",
        "bio": "Test biography",
        "status": "active",
        "visibility": "public",
        "verification_level": "unverified",
        "total_chats": 10,
        "total_messages": 50,
        "avg_fidelity": 0.85,
        "languages": ["en"],
        "default_language": "en",
        "auto_detect_language": True,
        "voice_id": "en_US-lessac-medium",
        "voice_enabled": True,
        "voice_speed": 1.0,
        "voice_pitch": 1.0,
    }


@pytest.fixture
def mock_api_key():
    """Mock API key data."""
    return {
        "id": "key-123",
        "user_id": "test-user-id-123",
        "name": "Test Key",
        "key_prefix": "pai_test123",
        "scopes": ["*"],
        "rate_limit": 1000,
        "daily_usage": 0,
        "last_used_at": None,
        "expires_at": None,
        "is_active": True,
    }


@pytest.fixture
def auth_headers(mock_user):
    """Create authorization headers with JWT token."""
    import jwt
    from datetime import datetime, timedelta
    
    secret = os.getenv("JWT_SECRET", "test-secret-key")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    
    payload = {
        "sub": mock_user["user_id"],
        "email": mock_user["email"],
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def api_key_headers():
    """Create API key headers."""
    return {"X-API-Key": "pai_test_api_key_12345678"}
