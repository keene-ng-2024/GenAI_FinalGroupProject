"""
vertex_orchestrator.py
----------------------
<<<<<<< HEAD
Vertex AI orchestrator for the multi-agent paper critique system.

This orchestrator uses Vertex AI (Gemini) models for all agent roles
and integrates with the grounding verifier for evidence-based critique.
=======
Main orchestrator for Vertex AI multi-agent critique pipeline.

This module runs the full agentic critique loop using Vertex AI models
and saves results to results/vertexai/
>>>>>>> vertexai
"""

from __future__ import annotations

import json
<<<<<<< HEAD
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

from src.agents.state import (
    create_initial_state,
    update_transcript,
    update_token_usage,
    increment_rounds,
    should_early_stop,
    get_latency_seconds,
)
from src.agents.vertex_client import (
    get_vertex_ai_client,
    generate_content,
    load_config,
)
from src.agents.personas import AgentRole, BaseAgent, build_agents
from src.agents.grounding_verifier import verify_all_grounding
=======
import os
import re
import sys
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.vertex_client import get_vertex_ai_client
from agents.grounding_verifier import verify_all_grounding
from agents.data_models import (
    Paper,
    CritiquePoint,
    StructuredReview,
    CritiqueResult
)

load_dotenv()
>>>>>>> vertexai


# ── Config ─────────────────────────────────────────────────────────────────────

def load_config(config_path: str = "config.yaml") -> dict:
<<<<<<< HEAD
    """Load configuration from YAML file."""
=======
>>>>>>> vertexai
    with open(config_path) as f:
        return yaml.safe_load(f)


<<<<<<< HEAD
# ── Output parsing ─────────────────────────────────────────────────────────────

def _parse_structured_output(raw: str) -> dict:
    """Parse the Summarizer's structured JSON output with fallbacks."""
=======
# ── Vertex AI Agent Implementation ─────────────────────────────────────────────

class VertexAIAgent:
    """Agent that uses Vertex AI models for critique generation."""
    
    def __init__(self, role: str, model_name: str, config: dict):
        self.role = role
        self.model_name = model_name
        self.config = config
        self.client = get_vertex_ai_client(config)
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    def _call_model(self, prompt: str, system_instruction: str = None) -> str:
        """Call Vertex AI model with the given prompt."""
        response = self.client.generate_content(
            prompt=prompt,
            system_instruction=system_instruction,
            model_name=self.model_name
        )
        self.total_input_tokens += response.input_tokens
        self.total_output_tokens += response.output_tokens
        return response.text
    
    def summarize_paper(self, paper_text: str) -> str:
        """Generate a summary of the paper."""
        prompt = f"""Summarize the following paper in 3-5 sentences:

{paper_text}

Summary:"""
        return self._call_model(prompt, "You are a helpful research assistant.")
    
    def generate_critique(self, summary: str) -> str:
        """Generate initial critique points based on the paper summary."""
        prompt = f"""Review the following paper summary and provide constructive critique.
Focus on potential issues with methodology, claims, or evidence.

Summary:
{summary}

Provide your critique as a list of specific points with supporting evidence."""
        return self._call_model(prompt, "You are an expert academic reviewer.")
    
    def audit(self, critique: str, summary: str) -> str:
        """Audit the critique and provide feedback."""
        prompt = f"""Review the following critique of a paper and provide feedback.
Check if the critique points are well-supported and identify any gaps.

Critique:
{critique}

Summary:
{summary}

Provide specific feedback on the critique quality."""
        return self._call_model(prompt, "You are a critical academic reviewer.")
    
    def revise_critique(self, audit_feedback: str) -> str:
        """Revise critique based on audit feedback."""
        prompt = f"""Revise your previous critique based on the following feedback:

Feedback:
{audit_feedback}

Provide an improved critique that addresses the feedback."""
        return self._call_model(prompt, "You are an expert academic reviewer.")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_structured_output(raw: str) -> dict:
    """Parse the Summariser's structured JSON output with fallbacks."""
>>>>>>> vertexai
    text = raw.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: extract the first JSON object with regex
<<<<<<< HEAD
    import re
=======
>>>>>>> vertexai
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Last resort: return an empty valid structure
    print("  [WARN] Failed to parse structured output, returning empty structure")
    return {
        "summary": "",
        "strengths": [],
        "weaknesses": [],
        "questions": [],
        "scores": {
            "correctness": 3,
            "novelty": 3,
            "recommendation": "borderline",
            "confidence": 1,
        },
    }


def _flatten_to_critique_points(structured: dict) -> dict[str, str]:
    """Convert structured output to flat critique_points dict for scorer compat."""
    points = {}
    idx = 1
    for item in structured.get("weaknesses", []):
        if isinstance(item, str):
            full = item
        elif isinstance(item, dict):
            point_text = item.get("point", "")
            evidence = item.get("evidence", "")
            full = f"{point_text}. {evidence}".strip(" .") if evidence else point_text
        else:
            continue
        points[f"point_{idx:03d}"] = full
        idx += 1
    return points


def _build_reviewer_scores_block(reviews: list[dict]) -> str:
<<<<<<< HEAD
    """Average the raw reviewer scores and format them as context for the Summarizer."""
    import numpy as np
    
=======
    """Average the raw reviewer scores and format them as context for the Summariser."""
>>>>>>> vertexai
    score_keys = ["Correctness", "Technical Novelty And Significance",
                  "Empirical Novelty And Significance", "Recommendation", "Confidence"]
    averages = {}
    for key in score_keys:
        vals = []
        for r in reviews:
            raw = r.get("scores", {}).get(key, "")
            try:
                vals.append(float(raw))
            except (ValueError, TypeError):
                continue
        if vals:
<<<<<<< HEAD
            averages[key] = round(np.mean(vals), 1)
=======
            averages[key] = round(sum(vals) / len(vals), 1)
>>>>>>> vertexai

    if not averages:
        return ""

    lines = ["Reviewer score averages (for context):"]
    for k, v in averages.items():
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)


<<<<<<< HEAD
# ── Vertex AI Agent ────────────────────────────────────────────────────────────

class VertexAgent:
    """Agent wrapper for Vertex AI with state management."""
    
    def __init__(
        self,
        name: str,
        role: AgentRole,
        system_prompt: str,
        model: str,
        config: dict,
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.model = model
        self.config = config
        self.client = get_vertex_ai_client(config=config)
        self.history: List[Dict[str, str]] = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    def chat(self, user_message: str) -> str:
        """Send a message and get a reply."""
        self.history.append({"role": "user", "content": user_message})
        
        response = generate_content(
            client=self.client,
            model=self.model,
            messages=self.history,
            config=self.config,
        )
        
        text = response.get("text", "")
        token_usage = response.get("token_usage", {})
        
        self.total_input_tokens += token_usage.get("input_tokens", 0)
        self.total_output_tokens += token_usage.get("output_tokens", 0)
        
        self.history.append({"role": "model", "content": text})
        return text
    
    def reset(self):
        """Clear conversation history."""
        self.history.clear()


# ── Main orchestrator ──────────────────────────────────────────────────────────

def run_pipeline(
    paper_id: str,
    paper_text: str,
    config: Optional[dict] = None,
) -> dict:
    """
    Run the full Vertex AI multi-agent critique pipeline for one paper.
    
    Args:
        paper_id: Unique identifier for the paper
        paper_text: Full paper text (may be truncated)
        config: Config dict loaded from config.yaml
        
    Returns:
        Critique result dict with structured output and metadata
    """
    if config is None:
        config = load_config()
    
    vertex_config = config.get("vertex_ai", {})
    max_rounds = config["agent"].get("max_rounds", 5)
    early_stop_phrases = config["agent"].get("early_stop_phrases", [])
    
    # Build agents with Vertex AI models
    agents = {
        "reader": VertexAgent(
            name="Reader",
            role=AgentRole.READER,
            system_prompt=(
                "You are a careful academic reader. "
                "When given a paper (or section of a paper), produce a structured "
                "summary with the following clearly labelled sections:\n\n"
                "## Problem & Motivation\n"
                "## Proposed Method\n"
                "## Methods\n"
                "## Results\n"
                "## Claimed Contributions\n\n"
                "Be factual and concise. Include specific numbers from experiments."
            ),
            model=vertex_config.get("reader_model", "gemini-1.5-flash"),
            config=config,
        ),
        "critic": VertexAgent(
            name="Critic",
            role=AgentRole.CRITIC,
            system_prompt=(
                "You are a rigorous peer reviewer for a top-tier ML/AI venue. "
                "Given a paper summary, identify substantive weaknesses in: "
                "novelty, methodology, evaluation, clarity, and reproducibility. "
                "For each point give: (a) the issue, (b) why it matters, "
                "(c) what evidence from the paper supports your concern. "
                "Be specific and actionable."
            ),
            model=vertex_config.get("critic_model", "gemini-1.5-pro"),
            config=config,
        ),
        "auditor": VertexAgent(
            name="Auditor",
            role=AgentRole.AUDITOR,
            system_prompt=(
                "You are a senior programme committee member auditing a peer review. "
                "Your job is to challenge poorly-supported critique points: "
                "ask for concrete evidence, flag over-interpretations, and identify "
                "any points that are actually addressed in the paper. "
                "Also highlight genuine issues the Critic may have missed. "
                "Be constructive but demanding."
            ),
            model=vertex_config.get("auditor_model", "gemini-1.5-flash"),
            config=config,
        ),
        "summarizer": VertexAgent(
            name="Summarizer",
            role=AgentRole.SUMMARIZER,
            system_prompt=(
                "You are a senior editor. Given a debate between a Critic and Auditor "
                "about a paper, synthesise their discussion into a final structured review.\n\n"
                "Output ONLY valid JSON matching this exact schema:\n"
                "{\n"
                '  "summary": "<2-3 sentence paper summary>",\n'
                '  "strengths": [\n'
                '    {"point": "<strength>", "evidence": "<supporting evidence from paper>"}\n'
                "  ],\n"
                '  "weaknesses": [\n'
                '    {"point": "<weakness>", "evidence": "<supporting evidence from paper>"}\n'
                "  ],\n"
                '  "questions": [\n'
                '    {"question": "<question for authors>", "motivation": "<why this matters>"}\n'
                "  ],\n"
                '  "scores": {\n'
                '    "correctness": <int 1-5>,\n'
                '    "novelty": <int 1-5>,\n'
                '    "recommendation": "<accept|borderline|reject>",\n'
                '    "confidence": <int 1-5>\n'
                "  }\n"
                "}\n\n"
                "Rules:\n"
                "- Include 3-8 strengths and 3-8 weaknesses (deduplicated).\n"
                "- Include 2-5 questions for the authors.\n"
                "- Base scores on the reviewer score context provided and the debate.\n"
                "- Output nothing except the JSON object. No markdown fences, no commentary."
            ),
            model=vertex_config.get("summariser_model", "gemini-1.5-pro"),
            config=config,
        ),
    }
    
    start_time = time.perf_counter()
    transcript: List[Dict[str, Any]] = []
    
    def log(role: str, content: str) -> None:
        transcript.append({"role": role, "content": content, "timestamp": time.time()})
        print(f"\n    [{role}]\n{content[:300]}{'...' if len(content) > 300 else ''}")
    
    # ── Step 1: Reader summarises ──────────────────────────────────────────────
    print(f"\n  [ROUND 0] Reading paper …")
    summary = agents["reader"].chat(f"Please summarise the following paper:\n\n{paper_text}")
    log("Reader", summary)
    
    # Update token usage
    transcript[-1]["input_tokens"] = agents["reader"].total_input_tokens
    transcript[-1]["output_tokens"] = agents["reader"].total_output_tokens
    
    # ── Step 2: Critic generates initial critique ──────────────────────────────
    print(f"\n  [ROUND 0] Critic generating initial points …")
    critique = agents["critic"].chat(
        f"Here is the paper summary:\n\n{summary}\n\nNow list your critique points."
    )
    log("Critic (initial)", critique)
    
=======
# ── Agentic loop with Vertex AI ────────────────────────────────────────────────

def run_vertex_ai_critique(
    paper_id: str,
    paper: dict,
    cfg: dict,
) -> dict:
    """Run the full multi-agent critique loop for one paper using Vertex AI.

    Args:
        paper_id: Unique identifier for the paper.
        paper:    Full paper dict from reviews_parsed.json
        cfg:      Config dict loaded from config.yaml.
    """
    start_time = time.perf_counter()

    max_rounds = cfg["agent"]["max_rounds"]
    truncate_chars = cfg["agent"].get("truncate_body_chars", 12000)
    early_stop_phrases = cfg["agent"].get("early_stop_phrases", [])
    
    # Get Vertex AI model mappings
    model_map = cfg["vertex_ai"]["models"]
    
    # Build agents with Vertex AI models
    agents = {
        "reader": VertexAIAgent("Reader", model_map["reader"], cfg),
        "critic": VertexAIAgent("Critic", model_map["critic"], cfg),
        "auditor": VertexAIAgent("Auditor", model_map["auditor"], cfg),
        "summarizer": VertexAIAgent("Summarizer", model_map["summarizer"], cfg),
    }
    
    transcript = []

    def log(role: str, content: str) -> None:
        transcript.append({"role": role, "content": content})
        print(f"\n    [{role}]\n{content[:300]}{'…' if len(content) > 300 else ''}")

    # Prepare paper text
    title = paper.get("title", paper_id)
    full_text = paper.get("full_text", "")
    paper_text = full_text[:truncate_chars] if full_text else paper.get("abstract", "")
    if not paper_text:
        paper_text = title

    # ── Step 1: Reader summarises ──────────────────────────────────────────────
    print(f"\n  [ROUND 0] Reading paper …")
    summary = agents["reader"].summarize_paper(f"Title: {title}\n\n{paper_text}")
    log("Reader", summary)

    # ── Step 2: Critic generates initial critique ──────────────────────────────
    print(f"\n  [ROUND 0] Critic generating initial points …")
    critique = agents["critic"].generate_critique(summary)
    log("Critic (initial)", critique)

>>>>>>> vertexai
    # ── Steps 3–4: Auditor ↔ Critic debate ────────────────────────────────────
    rounds_done = 0
    for round_num in range(1, max_rounds + 1):
        print(f"\n  [ROUND {round_num}] Auditor auditing …")
<<<<<<< HEAD
        audit_feedback = agents["auditor"].chat(
            f"Paper summary:\n{summary}\n\n"
            f"Critic's points:\n{critique}\n\n"
            "Challenge weak points and identify anything important that was missed."
        )
        log(f"Auditor (round {round_num})", audit_feedback)
        
        rounds_done = round_num
        
        # Check early stopping
        if should_early_stop(audit_feedback, early_stop_phrases):
            print(f"  [STOP] Auditor satisfied after round {round_num}.")
            break
        
        print(f"  [ROUND {round_num}] Critic revising …")
        critique = agents["critic"].chat(
            f"The Auditor has challenged some of your points:\n\n{audit_feedback}\n\n"
            "Revise or defend your critique points accordingly."
        )
        log(f"Critic (round {round_num})", critique)
    
    # ── Step 5: Summarizer consolidates ────────────────────────────────────────
    print(f"\n  [SUMMARISE] Consolidating debate …")
    
    # Build context: reviewer scores + full debate transcript
    reviewer_scores_block = _build_reviewer_scores_block([])
=======
        audit_feedback = agents["auditor"].audit(critique, summary)
        log(f"Auditor (round {round_num})", audit_feedback)

        rounds_done = round_num

        # Early stopping check
        feedback_lower = audit_feedback.lower()
        should_stop = False
        for phrase in early_stop_phrases:
            idx = feedback_lower.find(phrase)
            if idx >= 0:
                prefix = feedback_lower[max(0, idx - 15):idx]
                if any(neg in prefix for neg in ["not ", "no ", "don't ", "isn't ", "hardly "]):
                    continue
                should_stop = True
                break
        if should_stop:
            print(f"  [STOP] Auditor satisfied after round {round_num}.")
            break

        print(f"  [ROUND {round_num}] Critic revising …")
        critique = agents["critic"].revise_critique(audit_feedback)
        log(f"Critic (round {round_num})", critique)

    # ── Step 5: Summariser consolidates ────────────────────────────────────────
    print(f"\n  [SUMMARISE] Consolidating debate …")

    reviewer_scores_block = _build_reviewer_scores_block(paper.get("reviews", []))
>>>>>>> vertexai
    full_debate = "\n\n".join(
        f"=== {entry['role']} ===\n{entry['content']}" for entry in transcript
    )
    if reviewer_scores_block:
        full_debate = reviewer_scores_block + "\n\n" + full_debate
<<<<<<< HEAD
    
    raw_summary = agents["summarizer"].chat(
        f"Here is the full debate transcript:\n\n{full_debate}\n\n"
        "Produce the final structured review JSON."
    )
    log("Summarizer", raw_summary)
    
    # Parse structured output
    structured = _parse_structured_output(raw_summary)
    critique_points = _flatten_to_critique_points(structured)
    
    # Calculate latency and token usage
    latency_seconds = round(time.perf_counter() - start_time, 2)
    total_input = sum(a.total_input_tokens for a in agents.values())
    total_output = sum(a.total_output_tokens for a in agents.values())
    
    # Verify grounding
    grounding_scores = verify_all_grounding(raw_summary, {"full_text": paper_text}, config)
    
    return {
        "paper_id": paper_id,
        "model": vertex_config.get("critic_model", "gemini-1.5-pro"),
=======

    raw_summary = agents["summarizer"]._call_model(
        f"Consolidate this debate into a structured JSON review:\n\n{full_debate}",
        "Return a JSON object with summary, strengths, weaknesses, questions, and scores."
    )
    log("Summarizer", raw_summary)

    # Parse structured output
    structured = _parse_structured_output(raw_summary)
    critique_points = _flatten_to_critique_points(structured)

    # Collect total token usage
    total_input = sum(a.total_input_tokens for a in agents.values())
    total_output = sum(a.total_output_tokens for a in agents.values())

    latency_seconds = round(time.perf_counter() - start_time, 2)

    # Run grounding verification
    grounding_result = verify_all_grounding(
        json.dumps(critique_points),
        paper,
        cfg
    )

    return {
        "paper_id": paper_id,
        "title": title,
        "model": cfg["vertex_ai"]["models"]["critic"],
>>>>>>> vertexai
        "rounds": rounds_done,
        "latency_seconds": latency_seconds,
        "token_usage": {"input": total_input, "output": total_output},
        "transcript": transcript,
        "structured": structured,
        "critique_points": critique_points,
<<<<<<< HEAD
        "grounding_verifier_scores": grounding_scores,
        "run_metadata": {
            "latency_ms": latency_seconds * 1000,
            "timestamp": time.time(),
        },
=======
        "grounding_verifier_scores": grounding_result,
>>>>>>> vertexai
    }


# ── Main pipeline ──────────────────────────────────────────────────────────────

<<<<<<< HEAD
def run_all_papers(
    reviews_path: str,
    output_dir: str,
    config: Optional[dict] = None,
) -> None:
    """
    Run the Vertex AI critique pipeline for all papers.
    
    Args:
        reviews_path: Path to reviews_parsed.json
        output_dir: Output directory for results
        config: Config dict loaded from config.yaml
    """
    if config is None:
        config = load_config()
    
    with open(reviews_path) as f:
        all_papers: dict = json.load(f)
    
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
=======
def run_all_papers_vertex_ai(reviews_path: str, output_dir: str, cfg: dict) -> None:
    """Run Vertex AI critique pipeline on all papers."""
    with open(reviews_path) as f:
        all_papers: dict = json.load(f)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

>>>>>>> vertexai
    for paper_id, paper in all_papers.items():
        out_file = out_dir / f"{paper_id}.json"
        if out_file.exists():
            print(f"  [SKIP] {paper_id}")
            continue
<<<<<<< HEAD
        
        print(f"\n{'='*60}\n  [PAPER] {paper_id} — {paper.get('title', '')[:50]}\n{'='*60}")
        
        try:
            result = run_pipeline(
                paper_id=paper_id,
                paper_text=paper.get("full_text", ""),
                config=config,
            )
        except Exception as exc:
            print(f"\n  [ERROR] {paper_id} failed: {exc}")
            continue
        
        with open(out_file, "w") as f:
            json.dump(result, f, indent=2)
        
=======

        print(f"\n{'='*60}\n  [PAPER] {paper_id} — {paper.get('title', '')[:50]}\n{'='*60}")

        try:
            result = run_vertex_ai_critique(
                paper_id=paper_id,
                paper=paper,
                cfg=cfg,
            )
        except Exception as exc:
            print(f"\n  [ERROR] {paper_id} failed: {exc}")
            import traceback
            traceback.print_exc()
            continue

        with open(out_file, "w") as f:
            json.dump(result, f, indent=2)

>>>>>>> vertexai
        n_points = len(result["critique_points"])
        print(f"\n  [SAVED] {n_points} weakness points → {out_file}")
        print(f"  [COST]  {result['token_usage']['input']:,} in / "
              f"{result['token_usage']['output']:,} out tokens  "
              f"({result['latency_seconds']}s)")


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cfg = load_config()
<<<<<<< HEAD
    run_all_papers(
=======
    
    # Verify Vertex AI configuration
    if "vertex_ai" not in cfg:
        raise ValueError("Vertex AI configuration not found in config.yaml")
    
    print(f"Running Vertex AI critique pipeline...")
    print(f"Project: {cfg['vertex_ai']['project']}")
    print(f"Location: {cfg['vertex_ai']['location']}")
    print(f"Output directory: {cfg['results']['vertexai_dir']}")
    
    run_all_papers_vertex_ai(
>>>>>>> vertexai
        reviews_path=cfg["data"]["reviews_file"],
        output_dir=cfg["results"]["vertexai_dir"],
        cfg=cfg,
    )
