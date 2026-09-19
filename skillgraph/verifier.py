"""
SkillGraph — Stage 4: Clarifying Question Generation & Verification

This module acts on inferences produced in Stage 3:
  1. Identifies inferences classified as "NEEDS_VERIFICATION".
  2. Generates targeted clarifying questions using pre-authored templates
     (no LLM API call required).
  3. Collects and applies candidate responses to update inferences to:
     - "CONFIRMED"
     - "PARTIALLY_CONFIRMED"
     - "SKILL_GAP"
  4. Marks verified: true for answered inferences, and verified: false
     for unverified inferences (e.g. HIGH_CONFIDENCE or unasked SKILL_GAP).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ===================================================================
# Classification constants & response mapping
# ===================================================================

# Standard classifications
CONFIRMED = "CONFIRMED"
PARTIALLY_CONFIRMED = "PARTIALLY_CONFIRMED"
SKILL_GAP = "SKILL_GAP"
NEEDS_VERIFICATION = "NEEDS_VERIFICATION"
HIGH_CONFIDENCE = "HIGH_CONFIDENCE"

# Mapping candidate options to classification outcomes
RESPONSE_MAP = {
    "implemented it myself": CONFIRMED,
    "hands-on": CONFIRMED,
    "used a library/tool": PARTIALLY_CONFIRMED,
    "part of a framework": PARTIALLY_CONFIRMED,
    "not sure": SKILL_GAP,
}


# ===================================================================
# 1. Loading question templates
# ===================================================================

def load_question_templates(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load question templates from a JSON file.

    If path is None, loads the default question_templates.json from
    the skillgraph package directory.
    """
    if path is None:
        path = Path(__file__).parent / "question_templates.json"
    else:
        path = Path(path)

    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ===================================================================
# 2. Template selection & question generation
# ===================================================================

def select_template(
    inference: dict[str, Any],
    templates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Select the most appropriate template for a given inference.

    Note: Currently picks the default (first) template or selects by
    a simple heuristic. Template selection can be made smarter in the
    future (e.g. based on whether the missing skill is a tool, language,
    architecture concept, or protocol), but keeping it predictable and
    non-overengineered for now.
    """
    if not templates:
        raise ValueError("No question templates available.")
    return templates[0]


def generate_question(
    inference: dict[str, Any],
    templates: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate a clarifying question for a single inference object.

    Args:
        inference: An inference dict containing 'missing_skill' and
            'matched_resume_skill'.
        templates: List of loaded question templates.

    Returns:
        A dict with 'missing_skill', 'question', and 'options'.
    """
    template_data = select_template(inference, templates)
    template_text = template_data["template"]
    options = list(template_data.get("options", []))

    matched_skill = inference.get("matched_resume_skill") or "your related experience"
    missing_skill = inference.get("missing_skill", "")

    question_text = template_text.format(
        matched_resume_skill=matched_skill,
        missing_skill=missing_skill,
    )

    return {
        "missing_skill": missing_skill,
        "question": question_text,
        "options": options,
    }


def generate_all_questions(
    inferences: list[dict[str, Any]],
    templates: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Generate clarifying questions for all NEEDS_VERIFICATION inferences.

    Skips HIGH_CONFIDENCE and SKILL_GAP inferences entirely.

    Args:
        inferences: List of inference dicts from Stage 3.
        templates: Optional list of templates (loaded automatically if None).

    Returns:
        A list of generated question dicts.
    """
    if templates is None:
        templates = load_question_templates()

    questions: list[dict[str, Any]] = []
    for inf in inferences:
        if inf.get("classification") == NEEDS_VERIFICATION:
            q = generate_question(inf, templates)
            questions.append(q)
    return questions


# ===================================================================
# 3. Response verification
# ===================================================================

def apply_response(
    inference: dict[str, Any],
    selected_option: str,
) -> dict[str, Any]:
    """Apply the candidate's chosen response to update the inference.

    Args:
        inference: The original inference dict.
        selected_option: The string option selected by the user
            (e.g., 'Implemented it myself', 'Used a library/tool', 'Not sure').

    Returns:
        A copy of the inference dict with:
          - 'classification' updated to CONFIRMED, PARTIALLY_CONFIRMED,
            or SKILL_GAP.
          - 'verified' set to True.
          - 'selected_option' recorded.
    """
    updated = dict(inference)
    opt_key = selected_option.strip().lower()

    new_classification = RESPONSE_MAP.get(opt_key, SKILL_GAP)
    updated["classification"] = new_classification
    updated["verified"] = True
    updated["selected_option"] = selected_option
    return updated


def initialize_verification_status(
    inferences: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Ensure every inference in the list has a 'verified' field.

    HIGH_CONFIDENCE and SKILL_GAP are initially verified: False
    (or unverified by question), while NEEDS_VERIFICATION starts as
    verified: False until answered.
    """
    result = []
    for inf in inferences:
        item = dict(inf)
        if "verified" not in item:
            item["verified"] = False
        result.append(item)
    return result
