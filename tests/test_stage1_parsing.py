from __future__ import annotations

from pathlib import Path
from skillgraph.parser import extract_resume_text, segment_resume, clean_jd_text


def test_extract_resume_text(sample_docx: Path):
    text = extract_resume_text(sample_docx)
    assert isinstance(text, str)
    assert len(text) > 0
    assert "Priya Sharma" in text
    assert "FastAPI" in text
    assert "microservices" in text.lower()


def test_segment_resume(sample_docx: Path):
    text = extract_resume_text(sample_docx)
    statements = segment_resume(text)

    assert isinstance(statements, list)
    assert len(statements) >= 15

    # Check key expected statements are extracted
    found_summary = any("Full-stack engineer with 4+ years" in s for s in statements)
    found_microservices = any("microservices architecture" in s for s in statements)
    found_kafka = any("Apache Kafka" in s for s in statements)
    found_skills_list = any("FastAPI, Django, React" in s for s in statements)

    assert found_summary, "Summary statement not properly segmented"
    assert found_microservices, "Experience bullet not segmented properly"
    assert found_kafka, "Kafka project bullet not segmented properly"
    assert found_skills_list, "Skills section not segmented properly"


def test_clean_jd_text(sample_jd_text: str):
    cleaned = clean_jd_text(sample_jd_text)
    assert isinstance(cleaned, str)
    assert len(cleaned) > 0
    # Checks multiple consecutive spaces are collapsed
    assert "  " not in cleaned
    assert "Senior Backend Engineer" in cleaned
    assert "Requirements" in cleaned


def test_reject_invalid_docx_structure(tmp_path: Path):
    import zipfile
    import pytest

    # Create a zip file with random contents but no OpenXML document
    fake_docx = tmp_path / "fake.docx"
    with zipfile.ZipFile(fake_docx, "w") as zf:
        zf.writestr("test.txt", "not a real docx")

    with pytest.raises(ValueError, match="OpenXML document structure"):
        extract_resume_text(fake_docx)
