"""
test_llm_router.py
==================
Unit tests for LLM router module.
"""
import pytest
from unittest.mock import patch, MagicMock
from llm.router import chat_completion, chat_completion_stream


class TestChatCompletion:
    """Test chat completion function."""
    
    @patch("llm.router.groq_client")
    def test_groq_success(self, mock_groq):
        mock_groq.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Hello!"))]
        )
        
        messages = [{"role": "user", "content": "Hi"}]
        result = chat_completion(messages)
        
        assert result == "Hello!"
        mock_groq.chat.completions.create.assert_called_once()
    
    @patch("llm.router.groq_client")
    def test_groq_failure_fallback(self, mock_groq):
        mock_groq.chat.completions.create.side_effect = Exception("API error")
        
        with patch("llm.router.cerebras_client") as mock_cerebras:
            mock_cerebras.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="Fallback response"))]
            )
            
            messages = [{"role": "user", "content": "Hi"}]
            result = chat_completion(messages)
            
            assert result == "Fallback response"
    
    @patch("llm.router.groq_client")
    def test_all_providers_fail(self, mock_groq):
        mock_groq.chat.completions.create.side_effect = Exception("API error")
        
        with patch("llm.router.cerebras_client") as mock_cerebras:
            mock_cerebras.chat.completions.create.side_effect = Exception("API error")
            
            with patch("llm.router.genai") as mock_genai:
                mock_genai.GenerativeModel.return_value.generate_content.side_effect = Exception("API error")
                
                messages = [{"role": "user", "content": "Hi"}]
                
                with pytest.raises(Exception):
                    chat_completion(messages)


class TestChatCompletionStream:
    """Test streaming chat completion."""
    
    @patch("llm.router.groq_client")
    def test_stream_success(self, mock_groq):
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="Hello"))]
        
        mock_groq.chat.completions.create.return_value = [mock_chunk]
        
        messages = [{"role": "user", "content": "Hi"}]
        result = list(chat_completion_stream(messages))
        
        assert len(result) > 0
