"""
test_fidelity.py
================
Unit tests for fidelity evaluation module.
"""
import pytest
from services.ai.fidelity.evaluator import (
    evaluate_grounding,
    evaluate_consistency,
    detect_hallucination,
    calculate_fidelity_score,
)


class TestEvaluateGrounding:
    """Test grounding evaluation."""
    
    def test_grounded_response(self):
        response = "I work as a software engineer at Google."
        knowledge = [
            {"text": "I am a software engineer at Google", "score": 0.95},
        ]
        score = evaluate_grounding(response, knowledge)
        assert score > 0.7
    
    def test_ungrounded_response(self):
        response = "I am a professional basketball player."
        knowledge = [
            {"text": "I work as a software engineer", "score": 0.9},
        ]
        score = evaluate_grounding(response, knowledge)
        assert score < 0.5
    
    def test_empty_knowledge(self):
        response = "I love programming."
        score = evaluate_grounding(response, [])
        assert score == 0.0
    
    def test_partial_grounding(self):
        response = "I work at Google and I love playing piano."
        knowledge = [
            {"text": "I work at Google", "score": 0.95},
        ]
        score = evaluate_grounding(response, knowledge)
        assert 0.3 < score < 0.8


class TestEvaluateConsistency:
    """Test consistency evaluation."""
    
    def test_consistent_statements(self):
        statements = [
            "I work as a software engineer.",
            "My job is software engineering.",
            "I code for a living.",
        ]
        score = evaluate_consistency(statements)
        assert score > 0.7
    
    def test_inconsistent_statements(self):
        statements = [
            "I work as a software engineer.",
            "I am a professional chef.",
            "I teach mathematics.",
        ]
        score = evaluate_consistency(statements)
        assert score < 0.5
    
    def test_empty_statements(self):
        score = evaluate_consistency([])
        assert score == 1.0  # Empty is consistent


class TestDetectHallucination:
    """Test hallucination detection."""
    
    def test_no_hallucination(self):
        response = "I work at Google as a software engineer."
        knowledge = [
            {"text": "I work at Google", "score": 0.9},
            {"text": "I am a software engineer", "score": 0.85},
        ]
        result = detect_hallucination(response, knowledge)
        assert result["detected"] == False
    
    def test_hallucination_detected(self):
        response = "I won the Nobel Prize in Physics last year."
        knowledge = [
            {"text": "I work as a teacher", "score": 0.9},
        ]
        result = detect_hallucination(response, knowledge)
        assert result["detected"] == True
    
    def test_no_knowledge(self):
        response = "I love traveling the world."
        result = detect_hallucination(response, [])
        assert result["detected"] == False  # No knowledge to compare


class TestCalculateFidelityScore:
    """Test overall fidelity score calculation."""
    
    def test_high_fidelity(self):
        score = calculate_fidelity_score(
            grounding=0.9,
            consistency=0.85,
            hallucination=False,
        )
        assert score > 0.8
    
    def test_low_fidelity_with_hallucination(self):
        score = calculate_fidelity_score(
            grounding=0.5,
            consistency=0.6,
            hallucination=True,
        )
        assert score < 0.5
    
    def test_medium_fidelity(self):
        score = calculate_fidelity_score(
            grounding=0.6,
            consistency=0.7,
            hallucination=False,
        )
        assert 0.5 < score < 0.8
