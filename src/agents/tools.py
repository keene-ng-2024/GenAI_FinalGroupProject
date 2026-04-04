"""
tools.py
--------
Tool definitions that agents can invoke during the agentic loop.

Each tool is a plain Python function.  The tool registry maps tool names
(as the LLM will call them) to their implementations.

Available tools
  - summarise_section   : return a short summary of a text chunk
  - extract_claims      : pull out empirical claims from text
  - check_citation      : placeholder for citation-existence check
  - flag_missing_baselines : highlight missing baseline comparisons
"""

from __future__ import annotations

import os
import re

from openai import OpenAI
from dotenv import load_dotenv

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


# ── Tool implementations ───────────────────────────────────────────────────────

def summarise_section(text: str, max_sentences: int = 3) -> str:
    """Return a concise summary of the provided text."""
    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Summarise the following text in at most {max_sentences} sentences:\n\n{text}"
                ),
            }
        ],
    )
    return response.choices[0].message.content.strip()


def extract_claims(text: str) -> list[str]:
    """Extract a bullet list of empirical claims from text."""
    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    "List every empirical claim in the text below, one per line, "
                    "prefixed with '- '.\n\n" + text
                ),
            }
        ],
    )
    raw = response.choices[0].message.content.strip()
    return [line.lstrip("- ").strip() for line in raw.splitlines() if line.strip()]


def check_citation(claim: str, bibliography: str) -> str:
    """
    Placeholder: check whether a claim is supported by a citation in the bibliography.
    Returns 'SUPPORTED', 'UNSUPPORTED', or 'UNCLEAR'.
    """
    lowered = claim.lower()
    # Very naive heuristic — replace with a real retrieval step if needed
    if re.search(r"\[\d+\]|\(.*\d{4}\)", claim):
        return "SUPPORTED"
    if any(kw in lowered for kw in ["we show", "we demonstrate", "we prove"]):
        return "UNCLEAR"
    return "UNSUPPORTED"


def flag_missing_baselines(methods_section: str, results_section: str) -> list[str]:
    """
    Ask the LLM to identify baselines that appear in the methods but are absent
    from the results tables.
    """
    client = _get_client()
    prompt = (
        "Methods section:\n"
        f"{methods_section}\n\n"
        "Results section:\n"
        f"{results_section}\n\n"
        "List any baselines or comparisons mentioned in the methods that are "
        "missing from the results. One per line, prefixed with '- '."
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content.strip()
    return [line.lstrip("- ").strip() for line in raw.splitlines() if line.strip()]


# ── Tool registry ──────────────────────────────────────────────────────────────

TOOL_REGISTRY: dict[str, callable] = {
    "summarise_section": summarise_section,
    "extract_claims": extract_claims,
    "check_citation": check_citation,
    "flag_missing_baselines": flag_missing_baselines,
}


def call_tool(name: str, **kwargs) -> str:
    """Dispatch a tool call by name and return the result as a string."""
    if name not in TOOL_REGISTRY:
        return f"[ERROR] Unknown tool: {name}"
    try:
        result = TOOL_REGISTRY[name](**kwargs)
        if isinstance(result, list):
            return "\n".join(result) if result else "(none found)"
        return str(result)
    except Exception as exc:
        return f"[ERROR] Tool '{name}' raised: {exc}"
