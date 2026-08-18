"""
test_language_detector.py
=========================
Unit tests for language detection module.
"""
import pytest
from services.ai.language.detector import (
    detect_language,
    get_language_prompt_addition,
    detect_language_batch,
    get_supported_languages,
    SUPPORTED_LANGUAGES,
)


class TestDetectLanguage:
    """Test language detection function."""
    
    def test_detect_english(self):
        result = detect_language("Hello, how are you today?")
        assert result["code"] == "en"
        assert result["confidence"] > 0.5
    
    def test_detect_spanish(self):
        result = detect_language("Hola, ¿cómo estás hoy?")
        assert result["code"] == "es"
        assert result["confidence"] > 0.5
    
    def test_detect_french(self):
        result = detect_language("Bonjour, comment allez-vous?")
        assert result["code"] == "fr"
        assert result["confidence"] > 0.5
    
    def test_detect_german(self):
        result = detect_language("Hallo, wie geht es Ihnen?")
        assert result["code"] == "de"
        assert result["confidence"] > 0.5
    
    def test_detect_chinese(self):
        result = detect_language("你好，今天怎么样？")
        assert result["code"] == "zh"
        assert result["confidence"] > 0.5
    
    def test_detect_japanese(self):
        result = detect_language("こんにちは、今日はどうですか？")
        assert result["code"] == "ja"
        assert result["confidence"] > 0.5
    
    def test_detect_korean(self):
        result = detect_language("안녕하세요, 오늘 어떠세요?")
        assert result["code"] == "ko"
        assert result["confidence"] > 0.5
    
    def test_detect_arabic(self):
        result = detect_language("مرحبا، كيف حالك اليوم؟")
        assert result["code"] == "ar"
        assert result["confidence"] > 0.5
    
    def test_detect_russian(self):
        result = detect_language("Привет, как дела сегодня?")
        assert result["code"] == "ru"
        assert result["confidence"] > 0.5
    
    def test_empty_text(self):
        result = detect_language("")
        assert result["code"] == "en"  # Default
        assert result["confidence"] == 0.0
    
    def test_unknown_text(self):
        result = detect_language("12345")
        assert result["code"] == "en"  # Default


class TestGetLanguagePromptAddition:
    """Test language prompt generation."""
    
    def test_same_language(self):
        prompt = get_language_prompt_addition("en", ["en", "es"])
        assert "English" in prompt
    
    def test_different_language(self):
        prompt = get_language_prompt_addition("es", ["en", "es"])
        assert "Spanish" in prompt
    
    def test_unsupported_language(self):
        prompt = get_language_prompt_addition("xyz", ["en", "es"])
        assert "English" in prompt  # Falls back to first supported


class TestDetectLanguageBatch:
    """Test batch language detection."""
    
    def test_batch_detection(self):
        texts = [
            "Hello, how are you?",
            "Hola, ¿cómo estás?",
            "Bonjour, comment allez-vous?",
        ]
        results = detect_language_batch(texts)
        assert len(results) == 3
        assert results[0]["code"] == "en"
        assert results[1]["code"] == "es"
        assert results[2]["code"] == "fr"


class TestGetSupportedLanguages:
    """Test supported languages retrieval."""
    
    def test_get_all_languages(self):
        languages = get_supported_languages()
        assert len(languages) > 20
        assert "en" in [l["code"] for l in languages]
        assert "es" in [l["code"] for l in languages]
    
    def test_language_structure(self):
        languages = get_supported_languages()
        for lang in languages:
            assert "code" in lang
            assert "name" in lang
            assert "native_name" in lang
            assert "rtl" in lang


class TestSupportedLanguages:
    """Test SUPPORTED_LANGUAGES constant."""
    
    def test_has_english(self):
        assert "en" in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES["en"]["name"] == "English"
    
    def test_has_spanish(self):
        assert "es" in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES["es"]["name"] == "Spanish"
    
    def test_rtl_languages(self):
        rtl_langs = [k for k, v in SUPPORTED_LANGUAGES.items() if v["rtl"]]
        assert "ar" in rtl_langs
        assert "he" in rtl_langs
