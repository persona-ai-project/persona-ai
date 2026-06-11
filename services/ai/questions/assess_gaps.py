from datetime import datetime, timezone
from typing import Any

# Gap types taxonomy
EMPTY = "empty"
LOW_CONFIDENCE = "low_confidence"
STALE = "stale"

# Persona fields that matter — mapped to minimum requirements
FIELD_RULES = {
    "name":        {"min_length": 2},
    "profession":  {"min_length": 3},
    # "city":        {"min_length": 2},
    "hobbies":     {"min_list": 1},
    "goals":       {"min_list": 1},
    "personality": {"min_length": 10},
    "background":  {"min_length": 20},
}

# How many days before a field is considered stale
STALE_DAYS = 30


def assess_gaps(persona_json: dict) -> list[dict]:
    """
    Pure function — analyzes a persona JSON and returns a list of gap signals.
    Each gap signal tells the QuestionEngine what to ask about next.

    Args:
        persona_json: Dictionary containing user persona fields

    Returns:
        List of gap signals, each with field, gap_type, and reason
    """
    gaps = []
    now = datetime.now(timezone.utc)

    for field, rules in FIELD_RULES.items():
        value = persona_json.get(field)

        # Check EMPTY gap — field missing or blank
        if value is None or value == "" or value == [] or value == {}:
            gaps.append({
                "field": field,
                "gap_type": EMPTY,
                "reason": f"'{field}' is missing from persona"
            })
            continue

        # Check LOW_CONFIDENCE gap — value too short or too few items
        if "min_length" in rules:
            if isinstance(value, str) and len(value.strip()) < rules["min_length"]:
                gaps.append({
                    "field": field,
                    "gap_type": LOW_CONFIDENCE,
                    "reason": f"'{field}' is too short to be useful"
                })

        if "min_list" in rules:
            if isinstance(value, list) and len(value) < rules["min_list"]:
                gaps.append({
                    "field": field,
                    "gap_type": LOW_CONFIDENCE,
                    "reason": f"'{field}' has too few items"
                })

    # Check STALE gap — last updated too long ago
    updated_at = persona_json.get("updated_at")
    if updated_at:
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        days_old = (now - updated_at).days
        if days_old > STALE_DAYS:
            gaps.append({
                "field": "updated_at",
                "gap_type": STALE,
                "reason": f"Persona not updated in {days_old} days"
            })

    return gaps