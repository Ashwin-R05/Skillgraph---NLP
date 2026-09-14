"""
SkillGraph — Stage 2: Explicit Skill Extraction

This module scans resume statements and job descriptions, identifying
every explicitly mentioned skill using dictionary-based matching
against a curated skill gazetteer.

No inference is performed here — only literal matches (canonical names
and their synonyms) are returned.  Inference belongs to Stage 3.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import spacy

# ---------------------------------------------------------------------------
# Lazy-loaded spaCy model (shared with Stage 1 via module-level cache)
# ---------------------------------------------------------------------------
_nlp = None


def _get_nlp():
    """Return (and cache) the spaCy English pipeline."""
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# ---------------------------------------------------------------------------
# Skill dictionary loading
# ---------------------------------------------------------------------------

def load_skill_dictionary(path: str | Path | None = None) -> dict[str, list[str]]:
    """Load the skill dictionary from a JSON file.

    The file maps canonical skill names to lists of synonyms/variants.
    If *path* is ``None``, the default ``skill_dictionary.json`` bundled
    alongside this module is used.

    Args:
        path: Absolute or relative path to the JSON file.

    Returns:
        A dict mapping canonical names (str) to synonym lists (list[str]).
    """
    if path is None:
        path = Path(__file__).parent / "skill_dictionary.json"
    else:
        path = Path(path)

    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Internal: build a lookup index from the skill dictionary
# ---------------------------------------------------------------------------

def _build_synonym_index(
    skill_dictionary: dict[str, list[str]],
) -> list[tuple[str, str]]:
    """Build a list of (lowered_phrase, canonical_name) pairs.

    The list is sorted **longest phrase first** so that multi-word
    synonyms (e.g. "apache kafka") are matched before their substrings
    (e.g. "kafka").

    Each canonical name is also included as a phrase (lowered).
    """
    pairs: list[tuple[str, str]] = []
    for canonical, synonyms in skill_dictionary.items():
        # Add the canonical name itself as a matchable phrase
        pairs.append((canonical.lower(), canonical))
        for syn in synonyms:
            pairs.append((syn.lower(), canonical))

    # Longest first → greedy multi-word match wins
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


def _normalise_text(text: str) -> str:
    """Lower-case and collapse whitespace for matching purposes."""
    return re.sub(r"\s+", " ", text.lower()).strip()


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def extract_skills(
    text: str,
    skill_dictionary: dict[str, list[str]],
) -> list[str]:
    """Identify explicitly mentioned skills in *text*.

    The function performs two complementary passes:

    1. **Dictionary sweep** — scans the normalised text for every synonym
       and canonical phrase in the dictionary (longest match first).
       Matched spans are masked so shorter substrings don't double-count.

    2. **spaCy NER cross-check** — entities labelled ORG, PRODUCT, or
       GPE by the model are compared against the dictionary to catch
       capitalisation variants the sweep may have missed.

    Args:
        text: Free-form text (a resume bullet or JD paragraph).
        skill_dictionary: Canonical→synonyms mapping.

    Returns:
        A **deduplicated** list of canonical skill names found in the text.
    """
    if not text or not text.strip():
        return []

    norm = _normalise_text(text)
    synonym_index = _build_synonym_index(skill_dictionary)
    found: set[str] = set()

    # ── Pass 1: dictionary sweep (longest-match-first) ────────────────
    # We maintain a "mask" string of the same length where matched
    # regions are replaced with null chars so shorter overlapping
    # synonyms don't re-match.
    mask = list(norm)

    for phrase, canonical in synonym_index:
        if canonical in found:
            # Already matched via a longer synonym — skip scanning
            continue
        # Use word-boundary-aware search so "go" doesn't match "django"
        pattern = re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)")
        masked_str = "".join(mask)
        match = pattern.search(masked_str)
        if match:
            found.add(canonical)
            # Mask the matched span
            for i in range(match.start(), match.end()):
                mask[i] = "\x00"

    # ── Pass 2: spaCy NER cross-check ─────────────────────────────────
    nlp = _get_nlp()
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in {"ORG", "PRODUCT", "GPE", "WORK_OF_ART"}:
            ent_lower = ent.text.lower().strip()
            for phrase, canonical in synonym_index:
                if canonical in found:
                    continue
                if ent_lower == phrase:
                    found.add(canonical)
                    break

    return sorted(found)


# ---------------------------------------------------------------------------
# Resume-level extraction
# ---------------------------------------------------------------------------

def extract_resume_skills(
    resume_statements: list[str],
    skill_dictionary: dict[str, list[str]],
) -> list[dict[str, str]]:
    """Extract skills from each resume statement individually.

    Args:
        resume_statements: List of bullet-level strings (Stage 1 output).
        skill_dictionary: Canonical→synonyms mapping.

    Returns:
        A list of dicts, each with ``"skill"`` (canonical name) and
        ``"source_statement"`` (the original bullet it was found in).
        A skill appearing in multiple bullets will produce multiple entries.
    """
    results: list[dict[str, str]] = []
    for statement in resume_statements:
        skills = extract_skills(statement, skill_dictionary)
        for skill in skills:
            results.append({
                "skill": skill,
                "source_statement": statement,
            })
    return results


# ---------------------------------------------------------------------------
# JD-level extraction
# ---------------------------------------------------------------------------

def extract_jd_skills(
    job_description: str,
    skill_dictionary: dict[str, list[str]],
) -> list[str]:
    """Extract required skills from a full job description.

    Args:
        job_description: Cleaned JD text (Stage 1 output).
        skill_dictionary: Canonical→synonyms mapping.

    Returns:
        A flat, deduplicated list of canonical skill names.
    """
    return extract_skills(job_description, skill_dictionary)
