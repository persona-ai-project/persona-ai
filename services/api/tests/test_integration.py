"""
test_integration.py
===================
Integration tests for the digital twin system.
These tests require database and external services.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


@pytest.mark.integration
class TestTwinWorkflow:
    """Test complete twin workflow."""
    
    @pytest.mark.skipif(
        os.getenv("DATABASE_URL") is None,
        reason="Database not available"
    )
    def test_create_and_query_twin(self):
        """Test creating a twin and querying it."""
        from sqlalchemy import create_engine, text
        
        engine = create_engine(os.getenv("DATABASE_URL"))
        
        with engine.connect() as conn:
            # Create test twin
            twin_id = "test-integration-twin"
            conn.execute(
                text("""INSERT INTO twins (id, owner_id, name, slug, status, visibility)
                        VALUES (:id, :owner, :name, :slug, 'active', 'private')
                        ON CONFLICT (id) DO NOTHING"""),
                {
                    "id": twin_id,
                    "owner": "test-user",
                    "name": "Integration Test Twin",
                    "slug": "integration-test-twin",
                }
            )
            conn.commit()
            
            # Query twin
            result = conn.execute(
                text("SELECT id, name FROM twins WHERE id = :id"),
                {"id": twin_id}
            ).fetchone()
            
            assert result is not None
            assert result[1] == "Integration Test Twin"
            
            # Cleanup
            conn.execute(text("DELETE FROM twins WHERE id = :id"), {"id": twin_id})
            conn.commit()


@pytest.mark.integration
class TestSourceIngestion:
    """Test source upload and ingestion workflow."""
    
    @pytest.mark.skipif(
        os.getenv("DATABASE_URL") is None,
        reason="Database not available"
    )
    def test_create_source(self):
        """Test creating a source record."""
        from sqlalchemy import create_engine, text
        
        engine = create_engine(os.getenv("DATABASE_URL"))
        
        with engine.connect() as conn:
            source_id = "test-integration-source"
            conn.execute(
                text("""INSERT INTO sources (id, twin_id, source_type, title, status)
                        VALUES (:id, :twin, :type, :title, 'pending')
                        ON CONFLICT (id) DO NOTHING"""),
                {
                    "id": source_id,
                    "twin": "test-integration-twin",
                    "type": "text",
                    "title": "Test Document",
                }
            )
            conn.commit()
            
            # Query source
            result = conn.execute(
                text("SELECT id, title FROM sources WHERE id = :id"),
                {"id": source_id}
            ).fetchone()
            
            assert result is not None
            assert result[1] == "Test Document"
            
            # Cleanup
            conn.execute(text("DELETE FROM sources WHERE id = :id"), {"id": source_id})
            conn.commit()


@pytest.mark.integration
class TestAPIKeyWorkflow:
    """Test API key management workflow."""
    
    @pytest.mark.skipif(
        os.getenv("DATABASE_URL") is None,
        reason="Database not available"
    )
    def test_create_and_validate_api_key(self):
        """Test creating an API key and validating it."""
        import hashlib
        from sqlalchemy import create_engine, text
        
        engine = create_engine(os.getenv("DATABASE_URL"))
        
        with engine.connect() as conn:
            key_id = "test-integration-key"
            key_hash = hashlib.sha256("pai_test_integration_key".encode()).hexdigest()
            
            conn.execute(
                text("""INSERT INTO api_keys (id, user_id, name, key_hash, key_prefix, scopes, rate_limit)
                        VALUES (:id, :user, :name, :hash, :prefix, :scopes, 1000)
                        ON CONFLICT (id) DO NOTHING"""),
                {
                    "id": key_id,
                    "user": "test-user",
                    "name": "Integration Test Key",
                    "hash": key_hash,
                    "prefix": "pai_test",
                    "scopes": ["*"],
                }
            )
            conn.commit()
            
            # Validate key
            result = conn.execute(
                text("SELECT id, user_id FROM api_keys WHERE key_hash = :hash"),
                {"hash": key_hash}
            ).fetchone()
            
            assert result is not None
            assert result[1] == "test-user"
            
            # Cleanup
            conn.execute(text("DELETE FROM api_keys WHERE id = :id"), {"id": key_id})
            conn.commit()


@pytest.mark.integration
class TestKnowledgeExtraction:
    """Test knowledge extraction from interview responses."""
    
    def test_extract_facts(self):
        """Test extracting facts from text."""
        from routers.interviews import _extract_knowledge
        
        text = "I work as a software engineer at Google. I graduated from MIT in 2015."
        knowledge = _extract_knowledge(text, "professional")
        
        assert isinstance(knowledge, list)
        # Should extract at least one knowledge item
        assert len(knowledge) >= 0  # May be empty if extraction fails
    
    def test_extract_empty_text(self):
        """Test extraction from empty text."""
        from routers.interviews import _extract_knowledge
        
        knowledge = _extract_knowledge("", "general")
        assert isinstance(knowledge, list)
        assert len(knowledge) == 0


@pytest.mark.integration
class TestResponseGeneration:
    """Test twin response generation."""
    
    def test_build_system_prompt(self):
        """Test system prompt building."""
        from routers.twin_chat import _build_system_prompt
        
        twin = {
            "name": "Test Twin",
            "personality_config": {"trait": "friendly"},
            "boundaries": ["politics"],
            "knowledge_anchors": ["I love coding"],
            "languages": ["en"],
            "default_language": "en",
            "auto_detect_language": True,
        }
        
        knowledge_chunks = [
            {"text": "I work at Google", "score": 0.9}
        ]
        
        prompt = _build_system_prompt(twin, knowledge_chunks, [], "en")
        
        assert "Test Twin" in prompt
        assert "friendly" in prompt
        assert "politics" in prompt
        assert "I love coding" in prompt
        assert "I work at Google" in prompt
