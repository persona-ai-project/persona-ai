"""
services/ai/language/detector.py
================================
Language detection and multi-language support for Digital Twins.

Features:
- Automatic language detection
- Language configuration per twin
- Response language matching
- Translation support (via LLM)
"""
from __future__ import annotations

import re
from typing import Optional


# ── Supported Languages ─────────────────────────────────────────────────────────

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "rtl": False},
    "es": {"name": "Spanish", "native": "Español", "rtl": False},
    "fr": {"name": "French", "native": "Français", "rtl": False},
    "de": {"name": "German", "native": "Deutsch", "rtl": False},
    "it": {"name": "Italian", "native": "Italiano", "rtl": False},
    "pt": {"name": "Portuguese", "native": "Português", "rtl": False},
    "nl": {"name": "Dutch", "native": "Nederlands", "rtl": False},
    "ru": {"name": "Russian", "native": "Русский", "rtl": False},
    "zh": {"name": "Chinese", "native": "中文", "rtl": False},
    "ja": {"name": "Japanese", "native": "日本語", "rtl": False},
    "ko": {"name": "Korean", "native": "한국어", "rtl": False},
    "ar": {"name": "Arabic", "native": "العربية", "rtl": True},
    "hi": {"name": "Hindi", "native": "हिन्दी", "rtl": False},
    "tr": {"name": "Turkish", "native": "Türkçe", "rtl": False},
    "pl": {"name": "Polish", "native": "Polski", "rtl": False},
    "sv": {"name": "Swedish", "native": "Svenska", "rtl": False},
    "da": {"name": "Danish", "native": "Dansk", "rtl": False},
    "no": {"name": "Norwegian", "native": "Norsk", "rtl": False},
    "fi": {"name": "Finnish", "native": "Suomi", "rtl": False},
    "uk": {"name": "Ukrainian", "native": "Українська", "rtl": False},
    "cs": {"name": "Czech", "native": "Čeština", "rtl": False},
    "el": {"name": "Greek", "native": "Ελληνικά", "rtl": False},
    "he": {"name": "Hebrew", "native": "עברית", "rtl": True},
    "th": {"name": "Thai", "native": "ไทย", "rtl": False},
    "vi": {"name": "Vietnamese", "native": "Tiếng Việt", "rtl": False},
    "id": {"name": "Indonesian", "native": "Bahasa Indonesia", "rtl": False},
    "ms": {"name": "Malay", "native": "Bahasa Melayu", "rtl": False},
    "tl": {"name": "Filipino", "native": "Filipino", "rtl": False},
    "bn": {"name": "Bengali", "native": "বাংলা", "rtl": False},
    "ta": {"name": "Tamil", "native": "தமிழ்", "rtl": False},
    "te": {"name": "Telugu", "native": "తెలుగు", "rtl": False},
    "sw": {"name": "Swahili", "native": "Kiswahili", "rtl": False},
}


# ── Character Range Detection ───────────────────────────────────────────────────

LANG_RANGES = [
    # (regex_pattern, language_code, confidence)
    (r'[\u4e00-\u9fff]', 'zh', 0.9),  # Chinese characters
    (r'[\u3040-\u309f\u30a0-\u30ff]', 'ja', 0.95),  # Japanese hiragana/katakana
    (r'[\uac00-\ud7af]', 'ko', 0.95),  # Korean hangul
    (r'[\u0600-\u06ff\u0750-\u077f]', 'ar', 0.9),  # Arabic
    (r'[\u0590-\u05ff]', 'he', 0.9),  # Hebrew
    (r'[\u0e00-\u0e7f]', 'th', 0.9),  # Thai
    (r'[\u0900-\u097f]', 'hi', 0.8),  # Devanagari (Hindi)
    (r'[\u0980-\u09ff]', 'bn', 0.8),  # Bengali
    (r'[\u0b80-\u0bff]', 'ta', 0.8),  # Tamil
    (r'[\u0c00-\u0c7f]', 'te', 0.8),  # Telugu
    (r'[\u0400-\u04ff]', 'ru', 0.8),  # Cyrillic (Russian)
    (r'[\u0370-\u03ff]', 'el', 0.8),  # Greek
]


# ── Common Words Detection ──────────────────────────────────────────────────────

COMMON_WORDS = {
    "en": ["the", "is", "are", "was", "were", "have", "has", "had", "do", "does", "will", "would", "can", "could", "should", "may", "might", "shall", "must"],
    "es": ["el", "la", "los", "las", "es", "son", "está", "están", "tiene", "tienen", "hace", "puede", "debería", "ser", "estar", "haber"],
    "fr": ["le", "la", "les", "est", "sont", "a", "ont", "fait", "peut", "devrait", "être", "avoir", "faire", "dire", "aller", "voir"],
    "de": ["der", "die", "das", "ist", "sind", "hat", "haben", "kann", "soll", "sein", "haben", "werden", "machen", "sagen", "gehen", "sehen"],
    "it": ["il", "la", "le", "è", "sono", "ha", "hanno", "fa", "può", "dovrebbe", "essere", "avere", "fare", "dire", "andare", "vedere"],
    "pt": ["o", "a", "os", "as", "é", "são", "tem", "têm", "faz", "pode", "deveria", "ser", "ter", "fazer", "dizer", "ir", "ver"],
    "ru": ["и", "в", "не", "на", "что", "он", "как", "это", "по", "но", "из", "за", "от", "для", "при", "до"],
    "ja": ["の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "さ", "ある", "いる", "する", "なる"],
    "ko": ["이", "그", "저", "것", "수", "등", "들", "및", "약", "또", "더", "meta", "는", "에서", "을", "를"],
    "zh": ["的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很"],
}


def detect_language(text: str) -> dict:
    """
    Detect the language of input text.
    
    Returns:
        Dict with language code, name, confidence, and RTL flag
    """
    if not text or len(text.strip()) < 3:
        return {
            "code": "en",
            "name": "English",
            "confidence": 0.5,
            "rtl": False,
            "method": "default"
        }

    text_lower = text.lower()
    
    # 1. Check character ranges (highest confidence)
    for pattern, lang_code, confidence in LANG_RANGES:
        if re.search(pattern, text):
            lang_info = SUPPORTED_LANGUAGES.get(lang_code, {})
            return {
                "code": lang_code,
                "name": lang_info.get("name", lang_code),
                "confidence": confidence,
                "rtl": lang_info.get("rtl", False),
                "method": "character_range"
            }

    # 2. Check common words frequency
    scores = {}
    words = set(re.findall(r'\b\w+\b', text_lower))
    
    for lang_code, common in COMMON_WORDS.items():
        matches = len(words.intersection(set(common)))
        if matches > 0:
            scores[lang_code] = matches / len(common)

    if scores:
        best_lang = max(scores, key=scores.get)
        confidence = min(scores[best_lang] * 2, 0.9)  # Scale up but cap at 0.9
        lang_info = SUPPORTED_LANGUAGES.get(best_lang, {})
        return {
            "code": best_lang,
            "name": lang_info.get("name", best_lang),
            "confidence": confidence,
            "rtl": lang_info.get("rtl", False),
            "method": "common_words"
        }

    # 3. Default to English
    return {
        "code": "en",
        "name": "English",
        "confidence": 0.3,
        "rtl": False,
        "method": "default"
    }


def get_language_prompt_addition(language_code: str, twin_languages: list[str] | None = None) -> str:
    """
    Get prompt addition for language-aware responses.
    
    Args:
        language_code: Detected or configured language
        twin_languages: List of languages the twin supports
    
    Returns:
        String to add to system prompt
    """
    lang_info = SUPPORTED_LANGUAGES.get(language_code, SUPPORTED_LANGUAGES["en"])
    
    # Check if twin supports this language
    if twin_languages and language_code not in twin_languages:
        if twin_languages:
            supported = ", ".join(twin_languages[:3])
            return f"""Language Note: The user is writing in {lang_info['name']}, but this twin primarily responds in {SUPPORTED_LANGUAGES[twin_languages[0]]['name']}.
If you can respond in {lang_info['name']}, do so. Otherwise, respond in {SUPPORTED_LANGUAGES[twin_languages[0]]['name']} and briefly note the language difference."""
        else:
            return f"The user is writing in {lang_info['name']}. Respond in the same language."

    return f"Respond in {lang_info['name']} (the language the user is writing in)."


def format_language_name(code: str) -> str:
    """Get formatted language name."""
    lang = SUPPORTED_LANGUAGES.get(code, {})
    return lang.get("name", code.upper())


def get_supported_languages_list() -> list[dict]:
    """Get list of all supported languages."""
    return [
        {
            "code": code,
            "name": info["name"],
            "native": info["native"],
            "rtl": info["rtl"],
        }
        for code, info in SUPPORTED_LANGUAGES.items()
    ]


def is_rtl(language_code: str) -> bool:
    """Check if a language is right-to-left."""
    lang = SUPPORTED_LANGUAGES.get(language_code, {})
    return lang.get("rtl", False)
