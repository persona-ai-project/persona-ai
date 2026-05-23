import pytest
from datetime import datetime, timezone, timedelta
from services.ai.questions.assess_gaps import assess_gaps, EMPTY, LOW_CONFIDENCE, STALE


def test_empty_profession():
    """Empty profession field should return empty gap"""
    persona = {
        "name": "Bilal",
        "profession": "",
        "city": "Lahore",
        "hobbies": ["cricket"],
        "goals": ["start a company"],
        "personality": "I am friendly and hardworking",
        "background": "I grew up in Lahore and studied at GCU",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    gaps = assess_gaps(persona)
    gap_fields = [g["field"] for g in gaps]
    assert "profession" in gap_fields
    assert any(g["gap_type"] == EMPTY for g in gaps if g["field"] == "profession")


def test_empty_hobbies():
    """Empty hobbies list should return empty gap"""
    persona = {
        "name": "Bilal",
        "profession": "Engineer",
        "city": "Lahore",
        "hobbies": [],
        "goals": ["start a company"],
        "personality": "I am friendly and hardworking",
        "background": "I grew up in Lahore and studied at GCU",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    gaps = assess_gaps(persona)
    gap_fields = [g["field"] for g in gaps]
    assert "hobbies" in gap_fields


def test_low_confidence_name():
    """Very short name should return low_confidence gap"""
    persona = {
        "name": "B",
        "profession": "Engineer",
        "city": "Lahore",
        "hobbies": ["cricket"],
        "goals": ["start a company"],
        "personality": "I am friendly and hardworking",
        "background": "I grew up in Lahore and studied at GCU",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    gaps = assess_gaps(persona)
    assert any(g["field"] == "name" and g["gap_type"] == LOW_CONFIDENCE for g in gaps)


def test_stale_persona():
    """Persona not updated in 31 days should return stale gap"""
    persona = {
        "name": "Bilal",
        "profession": "Engineer",
        "city": "Lahore",
        "hobbies": ["cricket"],
        "goals": ["start a company"],
        "personality": "I am friendly and hardworking",
        "background": "I grew up in Lahore and studied at GCU",
        "updated_at": (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
    }
    gaps = assess_gaps(persona)
    assert any(g["gap_type"] == STALE for g in gaps)


def test_complete_persona_no_gaps():
    """Complete fresh persona should return no gaps"""
    persona = {
        "name": "Bilal",
        "profession": "Software Engineer",
        "city": "Lahore",
        "hobbies": ["cricket", "reading"],
        "goals": ["start a company"],
        "personality": "I am friendly and hardworking person",
        "background": "I grew up in Lahore and studied computer science at GCU",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    gaps = assess_gaps(persona)
    assert len(gaps) == 0


def test_missing_field_entirely():
    """Field not present at all should return empty gap"""
    persona = {
        "name": "Bilal",
        "city": "Lahore",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    gaps = assess_gaps(persona)
    gap_fields = [g["field"] for g in gaps]
    assert "profession" in gap_fields
    assert "hobbies" in gap_fields
    assert "goals" in gap_fields