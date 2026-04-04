"""Tests for grounding_verifier.py."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import MagicMock, patch
from agents.grounding_verifier import (
    GroundingResult,
    _parse_verification_response,
    _fallback_parse_verification,
    _extract_critique_points,
    should_stop_debate,
    verify_all_grounding,
)


def test_grounding_result_defaults():
    r = GroundingResult(is_supported=True, confidence=0.9, evidence_match_score=0.8)
    assert r.supporting_evidence is None


def test_parse_verification_response_valid_json():
    text = '{"is_supported": true, "confidence": 0.85, "evidence_match_score": 0.9, "reasoning": "ok"}'
    result = _parse_verification_response(text)
    assert result["is_supported"] is True
    assert result["confidence"] == 0.85


def test_parse_verification_response_embedded_json():
    text = 'Some preamble. {"is_supported": false, "confidence": 0.3, "evidence_match_score": 0.2} trailing text'
    result = _parse_verification_response(text)
    assert result["is_supported"] is False


def test_parse_verification_response_no_json():
    with pytest.raises(ValueError):
        _parse_verification_response("No JSON here at all.")


def test_fallback_parse_supported():
    text = "The claim is supported by the paper."
    result = _fallback_parse_verification(text)
    assert result["is_supported"] is True


def test_fallback_parse_not_supported():
    text = "This is not supported by any evidence."
    result = _fallback_parse_verification(text)
    assert result["is_supported"] is False


def test_extract_critique_points_bullet():
    text = "- Point one about novelty\n  Evidence here\n- Point two about methodology"
    points = _extract_critique_points(text)
    assert len(points) >= 2


def test_extract_critique_points_numbered():
    text = "1. First issue\n   Supporting detail\n2. Second issue"
    points = _extract_critique_points(text)
    assert len(points) >= 2


def test_should_stop_debate_triggers():
    phrases = ["no further concerns", "i am satisfied", "approve"]
    assert should_stop_debate("I am satisfied with the critique.", phrases) is True
    assert should_stop_debate("No further concerns remain.", phrases) is True


def test_should_stop_debate_no_trigger():
    phrases = ["no further concerns", "i am satisfied"]
    assert should_stop_debate("There are still many issues to address.", phrases) is False


def test_should_stop_debate_negation():
    phrases = ["no further concerns", "i am satisfied"]
    # "not satisfied" should NOT trigger early stop
    assert should_stop_debate("I am not satisfied with this review.", phrases) is False


def test_verify_all_grounding_empty_critique():
    config = {"vertex_ai": {"project": "test", "location": "us-central1"}}
    result = verify_all_grounding("", {"full_text": "paper text"}, config)
    assert result["points_verified"] == 0
    assert result["grounding_rate"] == 0.0
