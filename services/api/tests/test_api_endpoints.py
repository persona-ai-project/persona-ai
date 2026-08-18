"""
test_api_endpoints.py
=====================
Tests for API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Test health and status endpoints."""
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_register_missing_fields(self, client):
        response = client.post("/auth/register", json={})
        assert response.status_code == 422  # Validation error
    
    def test_login_missing_fields(self, client):
        response = client.post("/auth/login", json={})
        assert response.status_code == 422
    
    def test_login_invalid_credentials(self, client):
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [400, 401, 404]


class TestTwinEndpoints:
    """Test twin CRUD endpoints."""
    
    def test_list_twins_unauthorized(self, client):
        response = client.get("/twins")
        assert response.status_code == 403  # No auth header
    
    def test_list_twins_authorized(self, client, auth_headers):
        response = client.get("/twins", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
    
    def test_create_twin_missing_fields(self, client, auth_headers):
        response = client.post("/twins", json={}, headers=auth_headers)
        assert response.status_code == 422
    
    def test_get_twin_not_found(self, client, auth_headers):
        response = client.get("/twins/nonexistent", headers=auth_headers)
        assert response.status_code == 404


class TestVoiceEndpoints:
    """Test voice endpoints."""
    
    def test_list_voices(self, client):
        response = client.get("/voice/voices")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert "default" in data
    
    def test_transcribe_empty_file(self, client):
        response = client.post(
            "/voice/transcribe",
            files={"file": ("test.webm", b"", "audio/webm")}
        )
        assert response.status_code == 400


class TestSubscriptionEndpoints:
    """Test subscription endpoints."""
    
    def test_list_plans(self, client):
        response = client.get("/subscriptions/plans")
        assert response.status_code == 200
    
    def test_get_subscription_unauthorized(self, client):
        response = client.get("/subscriptions/me")
        assert response.status_code == 403


class TestEnterpriseEndpoints:
    """Test enterprise API endpoints."""
    
    def test_list_api_keys_unauthorized(self, client):
        response = client.get("/enterprise/api-keys")
        assert response.status_code == 403
    
    def test_list_api_keys_authorized(self, client, auth_headers):
        response = client.get("/enterprise/api-keys", headers=auth_headers)
        # May return 403 if not enterprise plan
        assert response.status_code in [200, 403]
    
    def test_get_plan(self, client, auth_headers):
        response = client.get("/enterprise/plan", headers=auth_headers)
        assert response.status_code == 200


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""
    
    def test_analytics_unauthorized(self, client):
        response = client.get("/analytics/overview")
        assert response.status_code == 403
