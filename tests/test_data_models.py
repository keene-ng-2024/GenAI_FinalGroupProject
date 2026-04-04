"""Tests for data_models.py dataclasses."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from agents.data_models import Paper, CritiquePoint, StructuredReview, AgentMessage, CritiqueResult


def test_paper_creation():
    p = Paper(paper_id="p001", title="Test", abstract="Abstract", full_text="Body")
    assert p.paper_id == "p001"
    assert p.reviews is None


def test_paper_with_reviews():
    reviews = [{"score": 5, "text": "Good paper"}]
    p = Paper(paper_id="p001", title="T", abstract="A", full_text="B", reviews=reviews)
    assert len(p.reviews) == 1


def test_critique_point_defaults():
    cp = CritiquePoint(point="Weak baseline", evidence="Table 2 shows only 1 baseline")
    assert cp.low_confidence is False


def test_critique_point_low_confidence():
    cp = CritiquePoint(point="Unclear", evidence="", low_confidence=True)
    assert cp.low_confidence is True


def test_structured_review():
    sr = StructuredReview(
        summary="A paper about NLP.",
        strengths=[CritiquePoint("Novel approach", "Section 3")],
        weaknesses=[CritiquePoint("Weak eval", "Table 1")],
        questions=[{"question": "Why?", "motivation": "Unclear"}],
        scores={"correctness": 3, "novelty": 4, "recommendation": "borderline", "confidence": 2},
    )
    assert len(sr.strengths) == 1
    assert len(sr.weaknesses) == 1
    assert sr.scores["recommendation"] == "borderline"


def test_agent_message_timestamp():
    msg = AgentMessage(role="critic", content="This paper has issues.")
    assert msg.timestamp > 0
    assert msg.tool_calls is None


def test_critique_result_fields():
    result = CritiqueResult(
        paper_id="p001",
        model="gemini-2.5-flash",
        rounds=3,
        latency_seconds=45.2,
        token_usage={"input": 1000, "output": 500},
        transcript=[],
        structured=StructuredReview("Summary", [], [], [], {}),
        critique_points={"point_001": "Weak baseline"},
        grounding_verifier_scores={"grounding_rate": 0.8},
        run_metadata={"latency_ms": 45200},
    )
    assert result.rounds == 3
    assert result.latency_seconds == 45.2
    assert "point_001" in result.critique_points
