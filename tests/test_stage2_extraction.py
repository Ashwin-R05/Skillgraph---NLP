from __future__ import annotations

from pathlib import Path
from skillgraph.parser import extract_resume_text, segment_resume
from skillgraph.extractor import (
    load_skill_dictionary,
    extract_resume_skills,
    extract_jd_skills,
)


def test_load_skill_dictionary(skill_dict: dict):
    assert isinstance(skill_dict, dict)
    assert len(skill_dict) > 20
    # Core skills must exist
    assert "Python" in skill_dict
    assert "FastAPI" in skill_dict
    assert "Docker" in skill_dict
    assert "PostgreSQL" in skill_dict


def test_extract_resume_skills(sample_docx: Path, skill_dict: dict):
    text = extract_resume_text(sample_docx)
    statements = segment_resume(text)
    resume_skills = extract_resume_skills(statements, skill_dict)

    assert isinstance(resume_skills, list)
    assert len(resume_skills) > 0

    extracted_names = {entry["skill"] for entry in resume_skills}
    # Verify key skills extracted from Priya Sharma's sample resume
    expected_skills = {
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Microservices",
        "Apache Kafka",
        "Apache Spark",
        "React",
        "Django",
        "Docker",
        "Kubernetes",
        "Redis",
        "AWS",
    }
    for expected in expected_skills:
        assert expected in extracted_names, f"Expected {expected} to be extracted from resume"

    # Verify each entry has skill and source_statement
    for entry in resume_skills:
        assert "skill" in entry
        assert "source_statement" in entry
        assert len(entry["source_statement"]) > 0


def test_extract_jd_skills(sample_jd_cleaned: str, skill_dict: dict):
    jd_skills = extract_jd_skills(sample_jd_cleaned, skill_dict)

    assert isinstance(jd_skills, list)
    assert len(jd_skills) >= 10

    expected_jd_skills = {
        "Python",
        "FastAPI",
        "Django",
        "PostgreSQL",
        "MySQL",
        "Redis",
        "Docker",
        "Kubernetes",
        "Apache Kafka",
        "RabbitMQ",
        "Microservices",
        "Distributed Systems",
    }
    for expected in expected_jd_skills:
        assert expected in jd_skills, f"Expected {expected} in extracted JD skills"
