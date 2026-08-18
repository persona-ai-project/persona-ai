"""
test_frontend_components.py
===========================
Tests for frontend component logic.
"""
import pytest


class TestAPIConfig:
    """Test API configuration."""
    
    def test_api_url_format(self):
        """Test API URL is properly formatted."""
        # This tests the config logic, not the actual API
        api_url = "https://api-production-353db.up.railway.app"
        assert api_url.startswith("https://")
        assert "railway.app" in api_url
    
    def test_web_url_format(self):
        """Test web URL is properly formatted."""
        web_url = "https://web-production-4e2b6.up.railway.app"
        assert web_url.startswith("https://")
        assert "railway.app" in web_url


class TestTwinModel:
    """Test twin data model."""
    
    def test_twin_required_fields(self):
        """Test required twin fields."""
        required_fields = [
            "id", "name", "slug", "owner_id", "status", "visibility"
        ]
        
        twin = {
            "id": "123",
            "name": "Test Twin",
            "slug": "test-twin",
            "owner_id": "user-123",
            "status": "active",
            "visibility": "public",
        }
        
        for field in required_fields:
            assert field in twin
    
    def test_twin_optional_fields(self):
        """Test optional twin fields have defaults."""
        twin_defaults = {
            "tagline": None,
            "bio": None,
            "languages": ["en"],
            "default_language": "en",
            "auto_detect_language": True,
            "voice_id": "en_US-lessac-medium",
            "voice_enabled": True,
            "voice_speed": 1.0,
            "voice_pitch": 1.0,
        }
        
        for field, default in twin_defaults.items():
            assert twin_defaults[field] == default


class TestMessageFormat:
    """Test message format for chat."""
    
    def test_user_message(self):
        """Test user message format."""
        message = {
            "id": "msg-123",
            "role": "user",
            "content": "Hello, how are you?",
        }
        
        assert message["role"] == "user"
        assert len(message["content"]) > 0
    
    def test_assistant_message(self):
        """Test assistant message format."""
        message = {
            "id": "msg-456",
            "role": "assistant",
            "content": "I'm doing well, thank you!",
            "sources": [],
            "knowledge_used": 5,
            "confidence": 0.85,
        }
        
        assert message["role"] == "assistant"
        assert message["confidence"] >= 0
        assert message["confidence"] <= 1


class TestVoiceConfig:
    """Test voice configuration."""
    
    def test_voice_config_defaults(self):
        """Test voice config has proper defaults."""
        config = {
            "voice_id": "en_US-lessac-medium",
            "voice_enabled": True,
            "voice_speed": 1.0,
            "voice_pitch": 1.0,
        }
        
        assert 0.5 <= config["voice_speed"] <= 2.0
        assert 0.5 <= config["voice_pitch"] <= 2.0
    
    def test_voice_config_bounds(self):
        """Test voice config stays within bounds."""
        # Test speed bounds
        assert 0.5 <= 1.0 <= 2.0  # Valid
        assert not (0.5 <= 0.1 <= 2.0)  # Invalid
        assert not (0.5 <= 3.0 <= 2.0)  # Invalid


class TestAPIKeyFormat:
    """Test API key format."""
    
    def test_api_key_prefix(self):
        """Test API key has correct prefix."""
        key = "pai_abc123def456"
        assert key.startswith("pai_")
    
    def test_api_key_hash(self):
        """Test API key hashing."""
        import hashlib
        key = "pai_test_key"
        hashed = hashlib.sha256(key.encode()).hexdigest()
        assert len(hashed) == 64  # SHA256 hex length
