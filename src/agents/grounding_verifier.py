"""
grounding_verifier.py
---------------------
<<<<<<< HEAD
Grounding verification for critique points using Vertex AI.

This module provides:
- verify_grounding(): Verify a single critique point
- verify_all_grounding(): Batch verification of multiple critique points
- Grounding score calculation with LLM sub-calls
=======
Grounding verification for critique points.

This module provides functions to verify that critique points are
properly grounded in the paper text using LLM-based verification.
>>>>>>> vertexai
"""

from __future__ import annotations

<<<<<<< HEAD
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.agents.vertex_client import get_vertex_ai_client, generate_content, load_config


# ── Data structures ────────────────────────────────────────────────────────────
=======
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vertex_client import get_vertex_ai_client

>>>>>>> vertexai

@dataclass
class GroundingResult:
    """Result of grounding verification for a single critique point."""
    is_supported: bool
    confidence: float
    evidence_match_score: float
    supporting_evidence: Optional[str] = None
<<<<<<< HEAD


# ── Core verification ────────────────────────────────────────────────────────

def verify_grounding(
    critique_point: Dict[str, str],
    paper_section: str,
    config: Optional[Dict[str, Any]] = None,
) -> GroundingResult:
    """
    Verify if a critique point is supported by evidence in the paper.
    
    Args:
        critique_point: Dict with "point" and "evidence" fields
        paper_section: Relevant section of the paper text
        config: Config dict with vertex_ai settings
        
    Returns:
        GroundingResult with is_supported, confidence, and evidence_match_score
    """
    if config is None:
        config = load_config()
    
    vertex_config = config.get("vertex_ai", {})
    model = vertex_config.get("grounding_verifier", {}).get("model", "gemini-1.5-flash")
    max_tokens = vertex_config.get("grounding_verifier", {}).get("max_tokens", 1024)
    
    point = critique_point.get("point", "")
    evidence = critique_point.get("evidence", "")
    
    # Build prompt for grounding verification
    prompt = f"""Analyze whether the critique point is supported by the provided paper section.

Critique Point: {point}
Claimed Evidence: {evidence}

Paper Section:
{paper_section[:2000]}  # Truncate for efficiency

Please evaluate:
1. Is the claimed evidence actually present in the paper section?
2. Does the evidence actually support the critique point?
3. What is your confidence level (0-1)?

Respond with JSON:
{{
  "is_supported": true/false,
  "confidence": 0.0-1.0,
  "evidence_match_score": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""
    
    client = get_vertex_ai_client(config=config)
    
    try:
        response = generate_content(
            client=client,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            config=config,
        )
        
        # Parse response
        text = response.get("text", "")
        
        # Try to parse JSON
        try:
            result = _parse_verification_response(text)
        except Exception:
            # Fallback parsing
            result = _fallback_parse_verification(text)
        
        return GroundingResult(
            is_supported=result.get("is_supported", False),
            confidence=result.get("confidence", 0.0),
            evidence_match_score=result.get("evidence_match_score", 0.0),
            supporting_evidence=result.get("reasoning"),
        )
        
    except Exception as e:
        print(f"  [ERROR] Grounding verification failed: {e}")
=======
    missing_evidence: Optional[str] = None


def verify_grounding(
    critique_point: str,
    paper_section: str,
    config: dict,
    max_evidence_length: int = 1000,
) -> GroundingResult:
    """
    Verify that a critique point is grounded in the paper.
    
    Args:
        critique_point: The critique point to verify
        paper_section: The relevant section of the paper
        config: Configuration dictionary
        max_evidence_length: Maximum length of evidence to consider
        
    Returns:
        GroundingResult with verification metrics
    """
    vertex_config = config.get("vertex_ai", {})
    model_name = vertex_config.get("grounding_verifier", {}).get("model", "gemini-1.5-flash-002")
    
    client = get_vertex_ai_client(config)
    
    prompt = f"""Analyze whether the following critique point is properly grounded in the provided paper section.

Critique Point:
"{critique_point}"

Paper Section:
"{paper_section[:max_evidence_length]}"

Please evaluate:
1. Is this critique point supported by evidence in the paper section?
2. What is your confidence level (0-1)?
3. What specific evidence from the paper supports or contradicts this point?

Respond in JSON format:
{{
    "is_supported": true/false,
    "confidence": 0.0-1.0,
    "supporting_evidence": "quote from paper if supported, null otherwise",
    "contradicting_evidence": "quote from paper if contradicted, null otherwise"
}}"""
    
    try:
        response = client.generate_content(
            prompt=prompt,
            model_name=model_name,
            max_tokens=1024,
        )
        
        # Parse JSON response
        text = response["text"].strip()
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            # Fallback parsing
            result = {
                "is_supported": "supported" in text.lower() and "not supported" not in text.lower(),
                "confidence": 0.5,
                "supporting_evidence": None,
                "contradicting_evidence": None,
            }
        
        return GroundingResult(
            is_supported=result.get("is_supported", False),
            confidence=result.get("confidence", 0.5),
            evidence_match_score=result.get("confidence", 0.5),
            supporting_evidence=result.get("supporting_evidence"),
            missing_evidence=result.get("contradicting_evidence"),
        )
        
    except Exception as e:
        print(f"  [WARN] Grounding verification failed: {e}")
>>>>>>> vertexai
        return GroundingResult(
            is_supported=False,
            confidence=0.0,
            evidence_match_score=0.0,
        )


<<<<<<< HEAD
def _parse_verification_response(text: str) -> Dict[str, Any]:
    """Parse JSON response from grounding verification."""
    # Try to find JSON in the response
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if match:
        import json
        return json.loads(match.group())
    raise ValueError("No JSON found in response")


def _fallback_parse_verification(text: str) -> Dict[str, Any]:
    """Fallback parsing for grounding verification response."""
    result = {
        "is_supported": False,
        "confidence": 0.0,
        "evidence_match_score": 0.0,
    }
    
    text_lower = text.lower()
    
    # Check for explicit indicators
    if "supported" in text_lower and "not supported" not in text_lower:
        result["is_supported"] = True
    
    # Try to extract confidence score
    confidence_match = re.search(r'confidence[:\s]+(\d+(?:\.\d+)?)', text_lower)
    if confidence_match:
        result["confidence"] = min(1.0, float(confidence_match.group(1)))
    
    # Try to extract evidence match score
    match_match = re.search(r'match[:\s]+(\d+(?:\.\d+)?)', text_lower)
    if match_match:
        result["evidence_match_score"] = min(1.0, float(match_match.group(1)))
    
    return result


# ── Batch verification ───────────────────────────────────────────────────────

def verify_all_grounding(
    critique_text: str,
    paper: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Verify grounding for all critique points in a critique text.
    
    Args:
        critique_text: Full critique text with multiple points
        paper: Paper dict with full_text
        config: Config dict with vertex_ai settings
        
    Returns:
        Dict with aggregate grounding scores
    """
    if config is None:
        config = load_config()
    
    # Extract individual critique points (simplified extraction)
    critique_points = _extract_critique_points(critique_text)
    
    total_confidence = 0.0
    supported_count = 0
    points_verified = 0
    
    for point in critique_points:
        # Find relevant paper section (simplified: use full text)
        paper_section = paper.get("full_text", "")[:5000]
        
        result = verify_grounding(point, paper_section, config)
        
        total_confidence += result.confidence
        if result.is_supported:
            supported_count += 1
        points_verified += 1
    
    # Calculate aggregates
    if points_verified > 0:
        avg_confidence = total_confidence / points_verified
        grounding_rate = supported_count / points_verified
    else:
        avg_confidence = 0.0
        grounding_rate = 0.0
    
    return {
        "avg_confidence": round(avg_confidence, 4),
        "grounding_rate": round(grounding_rate, 4),
        "points_verified": points_verified,
        "points_unsupported": points_verified - supported_count,
    }


def _extract_critique_points(critique_text: str) -> List[Dict[str, str]]:
    """Extract individual critique points from critique text."""
    points = []
    
    # Split by common separators
    lines = critique_text.split('\n')
    
    current_point = {"point": "", "evidence": ""}
    
    for line in lines:
        line = line.strip()
        
        # Check for point markers
        if re.match(r'^[-*]\s+', line) or re.match(r'^\d+\.\s+', line):
            # Save previous point if exists
            if current_point["point"]:
                points.append(current_point.copy())
            
            # Start new point
            current_point = {"point": line, "evidence": ""}
        elif line and current_point["point"]:
            # This is evidence for the current point
            if current_point["evidence"]:
                current_point["evidence"] += " " + line
            else:
                current_point["evidence"] = line
    
    # Save last point
    if current_point["point"]:
        points.append(current_point.copy())
    
    return points


# ── Early stopping detection ─────────────────────────────────────────────────

def should_stop_debate(
    audit_feedback: str,
    early_stop_phrases: List[str],
) -> bool:
    """
    Check if the debate should stop early based on auditor feedback.
    
    Args:
        audit_feedback: Auditor's feedback message
        early_stop_phrases: List of phrases that trigger early stopping
        
    Returns:
        True if early stopping should occur
    """
    feedback_lower = audit_feedback.lower()
    
    for phrase in early_stop_phrases:
        idx = feedback_lower.find(phrase)
        if idx >= 0:
            # Check for negation in context
            prefix = feedback_lower[max(0, idx - 15):idx]
            negations = ["not ", "no ", "don't ", "isn't ", "hardly "]
            if not any(neg in prefix for neg in negations):
                return True
    
    return False
=======
def verify_all_grounding(
    critique_text: str,
    paper: dict,
    config: dict,
) -> Dict[str, Any]:
    """
    Verify grounding for all critique points in a critique.
    
    Args:
        critique_text: JSON string of critique points
        paper: Paper dictionary with full_text
        config: Configuration dictionary
        
    Returns:
        Dictionary with grounding verification metrics
    """
    try:
        critique_points = json.loads(critique_text)
    except json.JSONDecodeError:
        critique_points = {}
    
    if not isinstance(critique_points, dict):
        critique_points = {}
    
    if not critique_points:
        return {
            "total_points": 0,
            "supported_points": 0,
            "avg_confidence": 0.0,
            "grounding_score": 0.0,
        }
    
    # Get paper text
    full_text = paper.get("full_text", "")
    abstract = paper.get("abstract", "")
    paper_text = full_text[:10000] if full_text else abstract  # Limit for efficiency
    
    # Verify each critique point
    results = []
    for point_id, point_text in critique_points.items():
        result = verify_grounding(point_text, paper_text, config)
        results.append(result)
    
    # Calculate metrics
    total_points = len(results)
    supported_points = sum(1 for r in results if r.is_supported)
    avg_confidence = sum(r.confidence for r in results) / total_points if total_points > 0 else 0.0
    
    # Grounding score: weighted combination of support rate and confidence
    grounding_score = (supported_points / total_points * 0.5 + avg_confidence * 0.5) if total_points > 0 else 0.0
    
    return {
        "total_points": total_points,
        "supported_points": supported_points,
        "unsupported_points": total_points - supported_points,
        "support_rate": supported_points / total_points if total_points > 0 else 0.0,
        "avg_confidence": avg_confidence,
        "grounding_score": grounding_score,
        "per_point_results": [
            {
                "point_id": point_id,
                "is_supported": r.is_supported,
                "confidence": r.confidence,
            }
            for point_id, r in zip(critique_points.keys(), results)
        ],
    }
>>>>>>> vertexai
