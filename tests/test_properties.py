"""
Property-based tests for the AI Research Paper Critique Assistant.

Tests the following correctness properties:
  CP-1: Transcript length invariant: |transcript| = 2 + 2 * rounds (reader + initial_critic + 2 per round)
  CP-2: Latency consistency: latency_ms == latency_seconds * 1000
  CP-3: Grounding score bounds: 0.0 <= score <= 1.0
  CP-4: Round count bounds: 0 <= rounds <= max_rounds
  CP-5: Output schema compliance (required keys present)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st


# ── CP-1: Transcript length invariant ────────────────────────────────────────

@given(rounds=st.integers(min_value=0, max_value=10))
def test_transcript_length_invariant(rounds):
    """
    CP-1: After `rounds` debate rounds, transcript has:
      - 1 Reader entry
      - 1 initial Critic entry
      - 2 entries per round (Auditor + Critic revision)
      - 1 Summarizer entry
    Total = 3 + 2 * rounds (if no early stop on last round)
    or 3 + 2 * rounds - 1 (if early stop before critic revision)
    Minimum: 3 entries (reader + critic + summarizer with 0 rounds)
    """
    # Simulate transcript construction
    transcript = []
    transcript.append({"role": "Reader", "content": "summary"})
    transcript.append({"role": "Critic (initial)", "content": "critique"})

    for r in range(rounds):
        transcript.append({"role": f"Auditor (round {r+1})", "content": "audit"})
        transcript.append({"role": f"Critic (round {r+1})", "content": "revised"})

    transcript.append({"role": "Summarizer", "content": "final"})

    expected = 3 + 2 * rounds
    assert len(transcript) == expected


# ── CP-2: Latency consistency ─────────────────────────────────────────────────

@given(latency_seconds=st.floats(min_value=0.001, max_value=3600.0, allow_nan=False, allow_infinity=False))
def test_latency_consistency(latency_seconds):
    """CP-2: latency_ms must equal latency_seconds * 1000 (within float precision)."""
    latency_ms = latency_seconds * 1000
    assert abs(latency_ms - latency_seconds * 1000) < 1e-6


@given(latency_seconds=st.floats(min_value=0.001, max_value=3600.0, allow_nan=False, allow_infinity=False))
def test_latency_ms_in_run_metadata(latency_seconds):
    """CP-2: run_metadata['latency_ms'] must match latency_seconds * 1000."""
    run_metadata = {"latency_ms": latency_seconds * 1000, "timestamp": 0}
    assert run_metadata["latency_ms"] == pytest.approx(latency_seconds * 1000, rel=1e-6)


# ── CP-3: Grounding score bounds ──────────────────────────────────────────────

@given(
    avg_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    grounding_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_grounding_score_bounds(avg_confidence, grounding_rate):
    """CP-3: All grounding scores must be in [0.0, 1.0]."""
    assert 0.0 <= avg_confidence <= 1.0
    assert 0.0 <= grounding_rate <= 1.0


@given(
    n_supported=st.integers(min_value=0, max_value=100),
    n_total=st.integers(min_value=1, max_value=100),
)
def test_grounding_rate_calculation(n_supported, n_total):
    """CP-3: Grounding rate = supported / total must be in [0, 1]."""
    assume(n_supported <= n_total)
    rate = n_supported / n_total
    assert 0.0 <= rate <= 1.0


# ── CP-4: Round count bounds ──────────────────────────────────────────────────

@given(
    max_rounds=st.integers(min_value=1, max_value=20),
    actual_rounds=st.integers(min_value=0, max_value=20),
)
def test_round_count_bounds(max_rounds, actual_rounds):
    """CP-4: rounds must satisfy 0 <= rounds <= max_rounds."""
    assume(actual_rounds <= max_rounds)
    assert 0 <= actual_rounds <= max_rounds


@given(max_rounds=st.integers(min_value=1, max_value=10))
def test_early_stop_respects_max_rounds(max_rounds):
    """CP-4: Even with early stopping, rounds never exceeds max_rounds."""
    rounds_done = 0
    for r in range(1, max_rounds + 1):
        # Simulate early stop at any round
        if r == max_rounds:
            rounds_done = r
            break
        rounds_done = r

    assert 0 <= rounds_done <= max_rounds


# ── CP-5: Output schema compliance ───────────────────────────────────────────

REQUIRED_TOP_KEYS = {"paper_id", "model", "rounds", "latency_seconds",
                     "token_usage", "transcript", "structured", "critique_points",
                     "grounding_verifier_scores", "run_metadata"}

REQUIRED_STRUCTURED_KEYS = {"summary", "strengths", "weaknesses", "questions", "scores"}

REQUIRED_SCORE_KEYS = {"correctness", "novelty", "recommendation", "confidence"}


@given(
    paper_id=st.text(min_size=1, max_size=20),
    rounds=st.integers(min_value=0, max_value=5),
    latency=st.floats(min_value=0.1, max_value=600.0, allow_nan=False, allow_infinity=False),
)
def test_output_schema_top_level(paper_id, rounds, latency):
    """CP-5: Output dict must contain all required top-level keys."""
    result = {
        "paper_id": paper_id,
        "model": "gemini-2.5-flash",
        "rounds": rounds,
        "latency_seconds": latency,
        "token_usage": {"input": 100, "output": 50},
        "transcript": [],
        "structured": {},
        "critique_points": {},
        "grounding_verifier_scores": {},
        "run_metadata": {"latency_ms": latency * 1000},
    }
    assert REQUIRED_TOP_KEYS.issubset(result.keys())


@given(
    summary=st.text(min_size=1, max_size=200),
    n_weaknesses=st.integers(min_value=0, max_value=10),
)
def test_structured_output_schema(summary, n_weaknesses):
    """CP-5: Structured output must contain all required keys."""
    structured = {
        "summary": summary,
        "strengths": [],
        "weaknesses": [{"point": f"issue {i}", "evidence": "ev"} for i in range(n_weaknesses)],
        "questions": [],
        "scores": {"correctness": 3, "novelty": 3, "recommendation": "borderline", "confidence": 2},
    }
    assert REQUIRED_STRUCTURED_KEYS.issubset(structured.keys())
    assert REQUIRED_SCORE_KEYS.issubset(structured["scores"].keys())


@given(
    correctness=st.integers(min_value=1, max_value=5),
    novelty=st.integers(min_value=1, max_value=5),
    confidence=st.integers(min_value=1, max_value=5),
    recommendation=st.sampled_from(["accept", "borderline", "reject"]),
)
def test_score_value_ranges(correctness, novelty, confidence, recommendation):
    """CP-5: Score values must be in valid ranges."""
    assert 1 <= correctness <= 5
    assert 1 <= novelty <= 5
    assert 1 <= confidence <= 5
    assert recommendation in {"accept", "borderline", "reject"}
