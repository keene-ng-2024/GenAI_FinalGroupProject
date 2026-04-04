"""Tests for vertex_orchestrator.py with mocked LLM calls."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
import pytest
from unittest.mock import MagicMock, patch


MOCK_STRUCTURED = {
    "summary": "A paper about NLP.",
    "strengths": [{"point": "Novel approach", "evidence": "Section 3"}],
    "weaknesses": [
        {"point": "Weak baseline", "evidence": "Table 1"},
        {"point": "No ablation", "evidence": "Section 4"},
        {"point": "Limited dataset", "evidence": "Section 5"},
    ],
    "questions": [{"question": "Why?", "motivation": "Unclear"}],
    "scores": {"correctness": 3, "novelty": 3, "recommendation": "borderline", "confidence": 2},
}


def _make_mock_agent(responses: list):
    """Create a mock VertexAgent that returns responses in sequence."""
    agent = MagicMock()
    agent.total_input_tokens = 100
    agent.total_output_tokens = 50
    agent.chat.side_effect = responses
    return agent


def test_parse_structured_output_valid():
    from agents.vertex_orchestrator import _parse_structured_output
    raw = json.dumps(MOCK_STRUCTURED)
    result = _parse_structured_output(raw)
    assert result["summary"] == "A paper about NLP."
    assert len(result["weaknesses"]) == 3


def test_parse_structured_output_with_fences():
    from agents.vertex_orchestrator import _parse_structured_output
    raw = f"```json\n{json.dumps(MOCK_STRUCTURED)}\n```"
    result = _parse_structured_output(raw)
    assert "weaknesses" in result


def test_parse_structured_output_fallback():
    from agents.vertex_orchestrator import _parse_structured_output
    result = _parse_structured_output("not valid json at all")
    assert "summary" in result
    assert "scores" in result


def test_flatten_to_critique_points():
    from agents.vertex_orchestrator import _flatten_to_critique_points
    points = _flatten_to_critique_points(MOCK_STRUCTURED)
    assert len(points) == 3
    assert "point_001" in points
    assert "point_003" in points


def test_flatten_string_weaknesses():
    from agents.vertex_orchestrator import _flatten_to_critique_points
    structured = {"weaknesses": ["Issue A", "Issue B"]}
    points = _flatten_to_critique_points(structured)
    assert len(points) == 2


def test_build_reviewer_scores_block_empty():
    from agents.vertex_orchestrator import _build_reviewer_scores_block
    result = _build_reviewer_scores_block([])
    assert result == ""


def test_build_reviewer_scores_block_with_data():
    from agents.vertex_orchestrator import _build_reviewer_scores_block
    reviews = [
        {"scores": {"Correctness": "4", "Technical Novelty And Significance": "3"}},
        {"scores": {"Correctness": "2", "Technical Novelty And Significance": "5"}},
    ]
    result = _build_reviewer_scores_block(reviews)
    assert "Correctness: 3.0" in result


def test_run_pipeline_mocked():
    """End-to-end test with all LLM calls mocked."""
    from agents.vertex_orchestrator import run_pipeline

    mock_responses = {
        "reader": ["Paper summary: This paper proposes a new method."],
        "critic": ["Critique: 1. Weak baseline. 2. No ablation."],
        "auditor": ["I am satisfied with the critique. No further concerns."],
        "summarizer": [json.dumps(MOCK_STRUCTURED)],
    }

    with patch("agents.vertex_orchestrator.VertexAgent") as MockAgent:
        def make_agent(name, role, system_prompt, model, config):
            agent = MagicMock()
            agent.name = name
            agent.total_input_tokens = 50
            agent.total_output_tokens = 25
            key = name.lower()
            agent.chat.side_effect = mock_responses.get(key, ["default response"])
            return agent

        MockAgent.side_effect = make_agent

        with patch("agents.vertex_orchestrator.verify_all_grounding", return_value={"grounding_rate": 0.8}):
            config = {
                "vertex_ai": {"project": "test", "location": "us-central1",
                               "reader_model": "gemini-2.5-flash-lite",
                               "critic_model": "gemini-2.5-flash",
                               "auditor_model": "gemini-2.5-flash-lite",
                               "summariser_model": "gemini-2.5-flash"},
                "agent": {"max_rounds": 3, "early_stop_phrases": ["i am satisfied", "no further concerns"]},
            }
            result = run_pipeline("paper_test", "Full paper text here.", config=config)

    assert result["paper_id"] == "paper_test"
    assert "critique_points" in result
    assert "structured" in result
    assert result["rounds"] >= 0
