"""
SkillGraph — Stage 3: Inference Engine

This module identifies skills required by a job description that are
NOT explicitly present in the candidate's resume, then infers which of
those "missing" skills are nonetheless likely present based on:
  1. Graph-based relationships between skills (NetworkX)
  2. Semantic similarity between the resume statement and the missing
     skill (Sentence-BERT, all-MiniLM-L6-v2)

Each inference is scored with a confidence percentage and a plain-English
explanation that traces back to the specific resume statement used.

No clarifying questions are generated here — that is Stage 4.
No resume rewriting is done here — that is Stage 5.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx
from sentence_transformers import SentenceTransformer, util

# ===================================================================
# TUNABLE CONSTANTS — adjust these to calibrate the scoring model
# ===================================================================

# Relative weight given to the graph edge weight vs. semantic similarity
# when computing the final confidence score.  Must sum to 1.0.
#
#   confidence = (GRAPH_WEIGHT * edge_weight
#                 + SEMANTIC_WEIGHT * cosine_similarity) * 100
#
# Increasing GRAPH_WEIGHT trusts the hand-curated graph more.
# Increasing SEMANTIC_WEIGHT trusts the language model more.
GRAPH_WEIGHT: float = 0.5
SEMANTIC_WEIGHT: float = 0.5

# Classification thresholds (inclusive boundaries)
#   confidence > HIGH_THRESHOLD        → HIGH_CONFIDENCE
#   LOW_THRESHOLD <= confidence <= HIGH → NEEDS_VERIFICATION
#   confidence < LOW_THRESHOLD          → SKILL_GAP
HIGH_THRESHOLD: int = 85
LOW_THRESHOLD: int = 40

# Default Sentence-BERT model (runs locally, no API calls)
DEFAULT_SBERT_MODEL: str = "all-MiniLM-L6-v2"


# ===================================================================
# 1. Loading the skill relationship graph
# ===================================================================

def load_skill_graph(path: str | Path | None = None) -> list[dict]:
    """Load the skill graph edge list from a JSON file.

    If *path* is ``None``, the default ``skill_graph.json`` bundled
    alongside this module is used.

    Returns:
        A list of edge dicts, each with "from", "to", and "weight".
    """
    if path is None:
        path = Path(__file__).parent / "skill_graph.json"
    else:
        path = Path(path)

    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_graph(skill_graph_edges: list[dict]) -> nx.DiGraph:
    """Build a NetworkX directed graph from the edge list.

    Each edge carries a ``weight`` attribute (float, 0.0–1.0) that
    represents how strongly the source skill implies familiarity with
    the target skill.  The graph is directed because implications can
    be asymmetric — e.g. knowing Docker strongly implies some
    Kubernetes exposure, but not vice versa at the same strength.

    Args:
        skill_graph_edges: List of dicts with "from", "to", "weight".

    Returns:
        A ``networkx.DiGraph`` with weighted edges.
    """
    G = nx.DiGraph()
    for edge in skill_graph_edges:
        G.add_edge(
            edge["from"],
            edge["to"],
            weight=float(edge["weight"]),
        )
    return G


# ===================================================================
# 2. Sentence-BERT model loading
# ===================================================================

_sbert_model = None


def load_sbert_model(model_name: str = DEFAULT_SBERT_MODEL) -> SentenceTransformer:
    """Load (and cache) the Sentence-BERT model.

    The model runs entirely locally — no API calls are made.
    """
    global _sbert_model
    if _sbert_model is None:
        _sbert_model = SentenceTransformer(model_name)
    return _sbert_model


# ===================================================================
# 3. Finding missing skills
# ===================================================================

def find_missing_skills(
    resume_skills: list[dict[str, str]],
    jd_required_skills: list[str],
) -> list[str]:
    """Return JD-required skills NOT found in the resume.

    Args:
        resume_skills: Stage 2 output — list of
            ``{"skill": "...", "source_statement": "..."}``.
        jd_required_skills: Flat list of canonical skill names from JD.

    Returns:
        Sorted list of canonical skill names present in the JD but
        absent from the resume.
    """
    resume_skill_names: set[str] = {entry["skill"] for entry in resume_skills}
    return sorted(
        skill for skill in jd_required_skills
        if skill not in resume_skill_names
    )


# ===================================================================
# 4. Core inference function
# ===================================================================

def _classify(confidence: float) -> str:
    """Map a confidence score to a human-readable classification.

    Thresholds are defined by HIGH_THRESHOLD and LOW_THRESHOLD at the
    top of this file.
    """
    if confidence > HIGH_THRESHOLD:
        return "HIGH_CONFIDENCE"
    elif confidence >= LOW_THRESHOLD:
        return "NEEDS_VERIFICATION"
    else:
        return "SKILL_GAP"


def _compute_semantic_similarity(
    statement: str,
    skill_name: str,
    model: SentenceTransformer,
) -> float:
    """Compute cosine similarity between a resume statement and a skill name.

    We embed *skill_name* as a short query and *statement* as the
    document, then return the cosine similarity (0.0–1.0).

    Args:
        statement: The resume bullet point text.
        skill_name: The canonical skill name (e.g. "OAuth").
        model: A loaded SentenceTransformer model.

    Returns:
        Cosine similarity in [0.0, 1.0].
    """
    embeddings = model.encode([statement, skill_name], convert_to_tensor=True)
    cosine_sim = util.cos_sim(embeddings[0], embeddings[1]).item()
    # Clamp to [0, 1] — cosine similarity can technically be negative
    return max(0.0, min(1.0, cosine_sim))


def infer_skill(
    missing_skill: str,
    resume_skills: list[dict[str, str]],
    graph: nx.DiGraph,
    model: SentenceTransformer,
) -> dict[str, Any]:
    """Infer whether a single missing skill is likely present.

    Algorithm:
    ---------
    1. Look up all direct predecessors (in-edges) of *missing_skill*
       in the skill graph.
    2. Filter to only those predecessors whose canonical name appears
       in the candidate's resume_skills.
    3. For each matching predecessor:
       a. Retrieve the graph edge weight (hand-curated, 0.0–1.0).
       b. Find the source_statement from resume_skills for that
          predecessor skill.
       c. Compute the Sentence-BERT cosine similarity between that
          source_statement and the missing_skill name.
       d. Combine into a confidence score using the formula:

            ┌──────────────────────────────────────────────────────┐
            │  confidence = ( GRAPH_WEIGHT   × edge_weight         │
            │               + SEMANTIC_WEIGHT × cosine_similarity ) │
            │               × 100                                   │
            └──────────────────────────────────────────────────────┘

          Where:
            - edge_weight (0.0–1.0): How strongly the graph says
              skill A implies skill B.  This is a hand-curated prior.
            - cosine_similarity (0.0–1.0): How semantically close the
              candidate's actual resume statement is to the missing
              skill's name.  This captures contextual relevance.
            - GRAPH_WEIGHT and SEMANTIC_WEIGHT (default 0.5 each):
              Tuneable constants that control the relative trust
              placed in the curated graph vs. the language model.
              Must sum to 1.0.

    4. If multiple predecessors match, select the one with the
       **highest** combined confidence (best evidence wins).
    5. If no graph neighbours are found at all, return SKILL_GAP with
       confidence 0 and a reasoning string explaining that nothing
       related was found.

    Args:
        missing_skill: Canonical name of the skill not found in resume.
        resume_skills: Stage 2 resume output (list of skill+statement
            dicts).
        graph: The NetworkX skill relationship graph.
        model: A loaded SentenceTransformer model.

    Returns:
        An inference dict with keys: missing_skill, matched_resume_skill,
        matched_statement, edge_weight, semantic_similarity, confidence,
        reasoning, classification.
    """
    # Build a quick lookup: skill_name → list of source_statements
    skill_to_statements: dict[str, list[str]] = {}
    for entry in resume_skills:
        skill_to_statements.setdefault(entry["skill"], []).append(
            entry["source_statement"]
        )

    resume_skill_names = set(skill_to_statements.keys())

    # ── Find graph predecessors that the candidate has ────────────────
    # predecessors(missing_skill) = nodes with an edge → missing_skill
    candidates: list[dict[str, Any]] = []

    if graph.has_node(missing_skill):
        for predecessor in graph.predecessors(missing_skill):
            if predecessor in resume_skill_names:
                edge_weight = graph[predecessor][missing_skill]["weight"]

                # For each source_statement mentioning this predecessor,
                # compute semantic similarity and keep the best one
                best_sim = 0.0
                best_stmt = ""
                for stmt in skill_to_statements[predecessor]:
                    sim = _compute_semantic_similarity(stmt, missing_skill, model)
                    if sim > best_sim:
                        best_sim = sim
                        best_stmt = stmt

                # ── Confidence formula (documented above) ─────────
                #
                #   confidence = (GRAPH_WEIGHT * edge_weight
                #                 + SEMANTIC_WEIGHT * cosine_similarity)
                #                * 100
                #
                # This blends the curated graph prior with the
                # language-model's contextual judgement.  The result
                # is a percentage in [0, 100].
                confidence = (
                    GRAPH_WEIGHT * edge_weight
                    + SEMANTIC_WEIGHT * best_sim
                ) * 100

                candidates.append({
                    "predecessor": predecessor,
                    "statement": best_stmt,
                    "edge_weight": round(edge_weight, 2),
                    "semantic_similarity": round(best_sim, 2),
                    "confidence": round(confidence),
                })

    # ── No graph neighbour found ──────────────────────────────────────
    if not candidates:
        return {
            "missing_skill": missing_skill,
            "matched_resume_skill": None,
            "matched_statement": None,
            "edge_weight": 0.0,
            "semantic_similarity": 0.0,
            "confidence": 0,
            "reasoning": (
                f"No related skill found in your resume that connects "
                f"to '{missing_skill}' in the skill graph. This appears "
                f"to be a genuine skill gap."
            ),
            "classification": "SKILL_GAP",
        }

    # ── Pick the best candidate (highest confidence) ──────────────────
    best = max(candidates, key=lambda c: c["confidence"])
    classification = _classify(best["confidence"])

    # ── Build human-readable reasoning ────────────────────────────────
    reasoning = (
        f"Your resume mentions '{best['predecessor']}' in the statement: "
        f"\"{best['statement']}\". "
        f"'{best['predecessor']}' is closely related to '{missing_skill}' "
        f"(graph weight: {best['edge_weight']}, "
        f"semantic similarity: {best['semantic_similarity']}). "
        f"Inferred with {best['confidence']}% confidence."
    )

    return {
        "missing_skill": missing_skill,
        "matched_resume_skill": best["predecessor"],
        "matched_statement": best["statement"],
        "edge_weight": best["edge_weight"],
        "semantic_similarity": best["semantic_similarity"],
        "confidence": best["confidence"],
        "reasoning": reasoning,
        "classification": classification,
    }


# ===================================================================
# 5. Full inference pipeline
# ===================================================================

def run_inference(
    stage2_output: dict[str, Any],
    graph: nx.DiGraph,
    model: SentenceTransformer,
) -> dict[str, Any]:
    """Run inference across all missing skills.

    Args:
        stage2_output: Dict with "resume_skills" and
            "jd_required_skills" (Stage 2 output format).
        graph: The NetworkX skill relationship graph.
        model: A loaded SentenceTransformer model.

    Returns:
        A dict with:
          - "inferences": list of inference objects for missing skills
          - "explicitly_matched": list of skills found in both resume
            and JD (no inference needed)
    """
    resume_skills = stage2_output["resume_skills"]
    jd_required_skills = stage2_output["jd_required_skills"]

    # Skills already matched explicitly
    resume_skill_names = {entry["skill"] for entry in resume_skills}
    explicitly_matched = sorted(
        skill for skill in jd_required_skills
        if skill in resume_skill_names
    )

    # Skills that need inference
    missing = find_missing_skills(resume_skills, jd_required_skills)

    # Run inference on each missing skill
    inferences = [
        infer_skill(missing_skill, resume_skills, graph, model)
        for missing_skill in missing
    ]

    return {
        "inferences": inferences,
        "explicitly_matched": explicitly_matched,
    }
