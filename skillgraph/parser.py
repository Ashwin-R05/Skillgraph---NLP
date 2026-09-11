"""
SkillGraph — Stage 1: Parsing & Segmentation

This module handles:
  1. Extracting raw text from resume files (PDF or DOCX).
  2. Segmenting the cleaned resume text into bullet-level statements.
  3. Cleaning job-description text for downstream stages.

No skill extraction, NER, or inference happens here — that belongs to
Stage 2+.
"""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber
from docx import Document
import spacy

# ---------------------------------------------------------------------------
# Lazy-loaded spaCy model (loaded once on first call to segment_resume)
# ---------------------------------------------------------------------------
_nlp = None


def _get_nlp():
    """Return (and cache) the spaCy English pipeline."""
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# ---------------------------------------------------------------------------
# Section-header patterns we want to strip from segmented output
# ---------------------------------------------------------------------------
_SECTION_HEADERS = re.compile(
    r"^("
    r"summary|objective|experience|education|projects?|skills?"
    r"|certifications?|awards?|publications?|interests?"
    r"|references?|work\s*experience|professional\s*experience"
    r"|technical\s*skills|core\s*competencies|languages?"
    r"|volunteer|activities|honors"
    r")[\s:]*$",
    re.IGNORECASE,
)

# Lines that are purely decorative (e.g. "----", "****", "====")
_DECORATIVE = re.compile(r"^[\s\-=_*•·|+#]{0,80}$")

# Bullet prefixes to normalise away
_BULLET_PREFIX = re.compile(r"^[\s]*[•▪▸◦‣⁃\-–—*►➤»]\s*")


# ===================================================================
# 1. Resume text extraction
# ===================================================================

def extract_resume_text(file_path: str | Path) -> str:
    """Extract and clean raw text from a resume file (PDF or DOCX).

    Args:
        file_path: Path to the resume file.  Supported extensions: .pdf, .docx.

    Returns:
        A single cleaned string with normalised whitespace and repaired
        line breaks introduced by PDF column layout.

    Raises:
        ValueError: If the file extension is not .pdf or .docx.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {path}")

    ext = path.suffix.lower()
    if ext == ".pdf":
        raw = _extract_pdf(path)
    elif ext == ".docx":
        raw = _extract_docx(path)
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. Use .pdf or .docx."
        )

    return _clean_raw_text(raw)


def _extract_pdf(path: Path) -> str:
    """Pull text from every page of a PDF using pdfplumber."""
    pages: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def _extract_docx(path: Path) -> str:
    """Pull text from every paragraph of a DOCX file."""
    doc = Document(str(path))
    return "\n".join(para.text for para in doc.paragraphs)


def _clean_raw_text(raw: str) -> str:
    """Normalise whitespace artefacts common in PDF/DOCX extraction.

    Steps:
      - Replace Windows-style \\r\\n with \\n.
      - Collapse runs of 3+ newlines into 2.
      - Re-join lines that were broken mid-sentence by PDF column layout
        (a lowercase letter or comma at end-of-line followed by a lowercase
        start on the next line).
      - Strip leading/trailing whitespace from each line.
      - Collapse multiple spaces into one.
    """
    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Re-join lines broken mid-sentence by PDF extraction
    # e.g. "managed a team of\nengineers" → "managed a team of engineers"
    text = re.sub(r"([a-z,])\n([a-z])", r"\1 \2", text)

    # Strip each line & collapse internal whitespace
    lines = [re.sub(r"  +", " ", line.strip()) for line in text.splitlines()]
    return "\n".join(lines).strip()


# ===================================================================
# 2. Resume segmentation
# ===================================================================

def segment_resume(resume_text: str) -> list[str]:
    """Split cleaned resume text into bullet-level statements.

    Each returned string represents one discrete item of experience,
    project contribution, or accomplishment.

    The function:
      - Splits on newlines first (preserving the author's intended breaks).
      - Uses spaCy sentence segmentation as a fallback for long run-on
        paragraphs (> 200 chars with no newline break).
      - Strips bullet-point prefixes so downstream stages see uniform text.
      - Filters out section headers (e.g. "PROJECTS", "SKILLS") and
        decorative separator lines.

    Args:
        resume_text: Cleaned resume text (output of extract_resume_text).

    Returns:
        A list of non-empty statement strings, one per bullet/line.
    """
    nlp = _get_nlp()
    raw_lines = resume_text.splitlines()

    statements: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Drop section headers and decorative lines
        if _SECTION_HEADERS.match(stripped):
            continue
        if _DECORATIVE.match(stripped):
            continue

        # Remove bullet prefixes
        cleaned = _BULLET_PREFIX.sub("", stripped).strip()
        if not cleaned:
            continue

        # If a line is very long and likely a run-on paragraph, split it
        # into sentences with spaCy.
        if len(cleaned) > 200:
            doc = nlp(cleaned)
            for sent in doc.sents:
                s = sent.text.strip()
                if s and not _SECTION_HEADERS.match(s) and not _DECORATIVE.match(s):
                    statements.append(s)
        else:
            statements.append(cleaned)

    return statements


# ===================================================================
# 3. Job-description cleaning
# ===================================================================

def clean_jd_text(jd_text: str) -> str:
    """Clean and normalise a job description string.

    The JD is kept as a single block of text (not segmented) — downstream
    stages will handle extraction against the full description.

    Args:
        jd_text: Raw job description text (plain string, not a file).

    Returns:
        A whitespace-normalised string with consistent line breaks.
    """
    text = jd_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [re.sub(r"  +", " ", line.strip()) for line in text.splitlines()]
    return "\n".join(lines).strip()
