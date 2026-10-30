from __future__ import annotations

from pathlib import Path
from skillgraph.parser import extract_resume_text, segment_resume
from skillgraph.extractor import extract_resume_skills, extract_jd_skills
from skillgraph.inference import run_inference


def test_graph_and_model_loading(skill_graph, sbert_model):
    assert skill_graph.number_of_nodes() >= 30
    assert skill_graph.number_of_edges() >= 30
    assert sbert_model is not None


def test_run_inference_pipeline(sample_docx: Path, sample_jd_cleaned: str, skill_dict, skill_graph, sbert_model):
    text = extract_resume_text(sample_docx)
    statements = segment_resume(text)
    resume_skills = extract_resume_skills(statements, skill_dict)
    jd_skills = extract_jd_skills(sample_jd_cleaned, skill_dict)

    stage2_output = {
        "resume_skills": resume_skills,
        "jd_required_skills": jd_skills,
    }

    result = run_inference(stage2_output, skill_graph, sbert_model)

    assert "explicitly_matched" in result
    assert "inferences" in result

    explicit = set(result["explicitly_matched"])
    assert "Python" in explicit
    assert "FastAPI" in explicit
    assert "Microservices" in explicit
    assert "Docker" in explicit

    inferences = result["inferences"]
    assert len(inferences) > 0

    valid_classifications = {"HIGH_CONFIDENCE", "NEEDS_VERIFICATION", "SKILL_GAP"}
    for inf in inferences:
        assert inf["classification"] in valid_classifications
        assert 0 <= inf["confidence"] <= 100
        assert "missing_skill" in inf
        assert "reasoning" in inf

        # Verify confidence formula matches (0.50 * w_graph + 0.50 * sim_sbert) * 100 within rounding precision
        w_g = inf["edge_weight"]
        sim_s = inf["semantic_similarity"]
        expected_conf = int(round((0.50 * w_g + 0.50 * sim_s) * 100))
        assert abs(inf["confidence"] - expected_conf) <= 1

        # Verify classification threshold logic (> 74 -> HIGH, >= 40 -> NEEDS_VERIFICATION, else SKILL_GAP)
        if inf["confidence"] > 74:
            assert inf["classification"] == "HIGH_CONFIDENCE"
        elif inf["confidence"] >= 40:
            assert inf["classification"] == "NEEDS_VERIFICATION"
        else:
            assert inf["classification"] == "SKILL_GAP"


def test_missing_skills_identified(sample_docx: Path, sample_jd_cleaned: str, skill_dict, skill_graph, sbert_model):
    text = extract_resume_text(sample_docx)
    statements = segment_resume(text)
    resume_skills = extract_resume_skills(statements, skill_dict)
    jd_skills = extract_jd_skills(sample_jd_cleaned, skill_dict)

    result = run_inference({"resume_skills": resume_skills, "jd_required_skills": jd_skills}, skill_graph, sbert_model)
    inferred_skills = {inf["missing_skill"] for inf in result["inferences"]}

    # Skills in JD not explicitly in resume
    assert "Distributed Systems" in inferred_skills
    assert "ETL" in inferred_skills
