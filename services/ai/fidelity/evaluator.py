"""
services/ai/fidelity/evaluator.py
================================
Fidelity evaluation system for Digital Twins.

Measures how accurately a twin represents the real person by analyzing:
- Grounding: Is the response supported by knowledge?
- Consistency: Does it align with known facts?
- Hallucination: Does it make up information?
- Personality: Does it match the configured personality?
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class FidelityScore:
    """Result of a fidelity evaluation."""
    overall: float  # 0.0 to 1.0
    grounding: float  # How well grounded in knowledge
    consistency: float  # Consistency with known facts
    hallucination: float  # Inverse of hallucination (1.0 = no hallucination)
    personality: float  # Match to configured personality
    confidence: float  # Confidence in the evaluation
    issues: list[str]  # List of detected issues
    suggestions: list[str]  # Suggestions for improvement


@dataclass
class EvaluationResult:
    """Full evaluation result with details."""
    score: FidelityScore
    knowledge_used: int
    knowledge_available: int
    sources_cited: int
    response_length: int
    evaluated_at: str


# ── Hallucination Patterns ──────────────────────────────────────────────────────

HALLUCINATION_INDICATORS = [
    # Specific claims without sourcing
    r"(?:I|we) (?:published|wrote|created|invented) (?:a |the )?(?:book|paper|study|article)",
    r"(?:I|we) (?:won|received|were awarded) (?:a |the )?(?:prize|award|medal|degree)",
    r"(?:I|we) (?:worked|was|were) at (?:Google|Apple|Microsoft|Amazon|Meta|Netflix)",
    r"(?:I|we) (?:earned|made|received) \$[\d,]+",
    r"(?:I|we) (?:graduated|studied) at (?:Harvard|MIT|Stanford|Yale|Princeton)",
    
    # Unverifiable claims
    r"(?:I|we) (?:always|never|definitely|certainly) (?:do|did|will|would)",
    r"(?:I|we) (?:know|believe|think) (?:for certain|definitely|absolutely)",
    
    # Fabricated statistics
    r"\d+(?:\.\d+)?%",
    r"\d+(?:,\d{3})+ (?:dollars|users|people|customers)",
]


def _detect_hallucination(response: str, knowledge: list[str]) -> tuple[float, list[str]]:
    """
    Detect potential hallucinations in a response.
    
    Returns:
        Tuple of (hallucination_score, list_of_issues)
        hallucination_score: 0.0 = no hallucination, 1.0 = definitely hallucinated
    """
    issues = []
    score = 0.0
    
    response_lower = response.lower()
    
    # Check for hallucination patterns
    for pattern in HALLUCINATION_INDICATORS:
        matches = re.findall(pattern, response, re.IGNORECASE)
        if matches:
            for match in matches:
                # Check if this claim is supported by knowledge
                supported = False
                for k in knowledge:
                    if match.lower() in k.lower() or any(word in k.lower() for word in match.lower().split() if len(word) > 3):
                        supported = True
                        break
                
                if not supported:
                    issues.append(f"Unverified claim: '{match}'")
                    score += 0.15
    
    # Check for specific numbers/dates not in knowledge
    numbers_in_response = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', response)
    numbers_in_knowledge = set()
    for k in knowledge:
        nums = re.findall(r'\d+(?:,\d{3})*(?:\.\d+)?', k)
        numbers_in_knowledge.update(nums)
    
    for num in numbers_in_response:
        if num not in numbers_in_knowledge and len(num) > 2:
            issues.append(f"Unverified number: {num}")
            score += 0.05
    
    # Check for first-person claims not in knowledge
    first_person_claims = re.findall(r'(?:I|we) (?:have|had|was|were|did|do|will|would|can|could)', response)
    if len(first_person_claims) > 3:
        # Many first-person claims - might be making things up
        score += 0.1
        issues.append("Multiple unverified first-person claims")
    
    return min(score, 1.0), issues


def _check_grounding(response: str, knowledge: list[str]) -> float:
    """
    Check how well the response is grounded in provided knowledge.
    
    Returns:
        Grounding score: 0.0 = not grounded, 1.0 = fully grounded
    """
    if not knowledge:
        return 0.5  # Can't evaluate without knowledge
    
    response_words = set(response.lower().split())
    
    # Check overlap with knowledge
    grounded_phrases = 0
    total_knowledge = len(knowledge)
    
    for k in knowledge:
        k_words = set(k.lower().split())
        overlap = len(response_words & k_words) / max(len(k_words), 1)
        if overlap > 0.3:  # 30% word overlap indicates grounding
            grounded_phrases += 1
    
    return min(grounded_phrases / max(total_knowledge, 1), 1.0)


def _check_consistency(response: str, knowledge: list[str]) -> float:
    """
    Check consistency with known facts.
    
    Returns:
        Consistency score: 0.0 = inconsistent, 1.0 = fully consistent
    """
    if not knowledge:
        return 0.5
    
    response_lower = response.lower()
    
    # Check for contradictions
    contradictions = 0
    for k in knowledge:
        k_lower = k.lower()
        
        # Simple negation detection
        if "not" in k_lower and "not" not in response_lower:
            if any(word in response_lower for word in k_lower.split() if len(word) > 4):
                contradictions += 1
        elif "not" not in k_lower and "not" in response_lower:
            if any(word in k_lower for word in response_lower.split() if len(word) > 4):
                contradictions += 1
    
    consistency = 1.0 - (contradictions / max(len(knowledge), 1) * 0.5)
    return max(consistency, 0.0)


def _check_personality(response: str, personality_config: dict | None) -> float:
    """
    Check if response matches configured personality.
    
    Returns:
        Personality score: 0.0 = mismatch, 1.0 = perfect match
    """
    if not personality_config:
        return 0.7  # Default score when no personality configured
    
    score = 0.7  # Base score
    
    # Check tone indicators
    tone = personality_config.get("tone", "").lower()
    if tone:
        if "formal" in tone and any(word in response.lower() for word in ["hey", "gonna", "wanna", "lol"]):
            score -= 0.2
        elif "casual" in tone and any(word in response.lower() for word in ["therefore", "furthermore", "moreover"]):
            score -= 0.1
        elif "friendly" in tone and any(word in response.lower() for word in ["no", "wrong", "incorrect"]):
            score -= 0.1
    
    # Check style indicators
    style = personality_config.get("style", "").lower()
    if style:
        if "concise" in style and len(response.split()) > 100:
            score -= 0.15
        elif "verbose" in style and len(response.split()) < 20:
            score -= 0.1
    
    return max(min(score, 1.0), 0.0)


def evaluate_fidelity(
    response: str,
    knowledge: list[str],
    personality_config: dict | None = None,
    sources_cited: int = 0,
) -> EvaluationResult:
    """
    Evaluate the fidelity of a twin's response.
    
    Args:
        response: The twin's response text
        knowledge: List of knowledge items used
        personality_config: Twin's personality configuration
        sources_cited: Number of sources cited in response
    
    Returns:
        EvaluationResult with scores and analysis
    """
    # Run evaluations
    hallucination_score, hallucination_issues = _detect_hallucination(response, knowledge)
    grounding_score = _check_grounding(response, knowledge)
    consistency_score = _check_consistency(response, knowledge)
    personality_score = _check_personality(response, personality_config)
    
    # Calculate overall score (weighted average)
    overall = (
        grounding_score * 0.3 +
        consistency_score * 0.25 +
        (1.0 - hallucination_score) * 0.3 +
        personality_score * 0.15
    )
    
    # Generate suggestions
    suggestions = []
    if grounding_score < 0.5:
        suggestions.append("Response could be more grounded in provided knowledge")
    if hallucination_score > 0.3:
        suggestions.append("Response may contain unverified claims")
    if consistency_score < 0.7:
        suggestions.append("Response may conflict with known facts")
    if personality_score < 0.6:
        suggestions.append("Response could better match the configured personality")
    if sources_cited == 0 and len(knowledge) > 0:
        suggestions.append("Consider citing sources when using knowledge")
    
    # Calculate confidence
    confidence = 0.7  # Base confidence
    if len(knowledge) > 5:
        confidence += 0.1
    if sources_cited > 0:
        confidence += 0.1
    if len(response) > 50:
        confidence += 0.1
    
    return EvaluationResult(
        score=FidelityScore(
            overall=round(overall, 3),
            grounding=round(grounding_score, 3),
            consistency=round(consistency_score, 3),
            hallucination=round(1.0 - hallucination_score, 3),
            personality=round(personality_score, 3),
            confidence=round(min(confidence, 1.0), 3),
            issues=hallucination_issues,
            suggestions=suggestions,
        ),
        knowledge_used=len(knowledge),
        knowledge_available=len(knowledge),
        sources_cited=sources_cited,
        response_length=len(response),
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_response_batch(
    responses: list[dict],
    knowledge: list[str],
    personality_config: dict | None = None,
) -> list[EvaluationResult]:
    """
    Evaluate a batch of responses.
    
    Args:
        responses: List of dicts with 'response' and optional 'sources_cited'
        knowledge: List of knowledge items
        personality_config: Twin's personality configuration
    
    Returns:
        List of EvaluationResult
    """
    results = []
    for item in responses:
        result = evaluate_fidelity(
            response=item.get("response", ""),
            knowledge=knowledge,
            personality_config=personality_config,
            sources_cited=item.get("sources_cited", 0),
        )
        results.append(result)
    return results


def calculate_twin_fidelity(evaluations: list[EvaluationResult]) -> dict:
    """
    Calculate overall twin fidelity from multiple evaluations.
    
    Returns:
        Dict with aggregate scores and stats
    """
    if not evaluations:
        return {
            "overall": 0.0,
            "grounding": 0.0,
            "consistency": 0.0,
            "hallucination": 0.0,
            "personality": 0.0,
            "total_evaluations": 0,
            "avg_response_length": 0,
            "common_issues": [],
        }
    
    # Aggregate scores
    overall = sum(e.score.overall for e in evaluations) / len(evaluations)
    grounding = sum(e.score.grounding for e in evaluations) / len(evaluations)
    consistency = sum(e.score.consistency for e in evaluations) / len(evaluations)
    hallucination = sum(e.score.hallucination for e in evaluations) / len(evaluations)
    personality = sum(e.score.personality for e in evaluations) / len(evaluations)
    
    # Common issues
    all_issues = []
    for e in evaluations:
        all_issues.extend(e.score.issues)
    
    issue_counts = {}
    for issue in all_issues:
        # Normalize issue text
        normalized = issue.split(":")[0].strip()
        issue_counts[normalized] = issue_counts.get(normalized, 0) + 1
    
    common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "overall": round(overall, 3),
        "grounding": round(grounding, 3),
        "consistency": round(consistency, 3),
        "hallucination": round(hallucination, 3),
        "personality": round(personality, 3),
        "total_evaluations": len(evaluations),
        "avg_response_length": sum(e.response_length for e in evaluations) / len(evaluations),
        "common_issues": [{"issue": i[0], "count": i[1]} for i in common_issues],
    }
