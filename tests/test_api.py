from __future__ import annotations

import io
from pathlib import Path


def test_api_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "SkillGraph" in data["service"]


def test_api_analyze_bad_file_type(client, sample_jd_text: str):
    data = {
        "resume": (io.BytesIO(b"Candidate text content"), "resume.txt"),
        "job_description": sample_jd_text,
    }
    response = client.post(
        "/api/analyze",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    json_data = response.get_json()
    assert "error" in json_data
    assert "Unsupported file type" in json_data["error"]


def test_api_analyze_file_over_5mb(client, sample_jd_text: str):
    # Create dummy in-memory content larger than 5 MB
    large_content = b"0" * (5 * 1024 * 1024 + 1024)  # 5 MB + 1 KB
    data = {
        "resume": (io.BytesIO(large_content), "large_resume.docx"),
        "job_description": sample_jd_text,
    }
    response = client.post(
        "/api/analyze",
        data=data,
        content_type="multipart/form-data",
    )
    assert response.status_code == 413
    json_data = response.get_json()
    assert "error" in json_data
    assert "5 MB" in json_data["error"]


def test_api_analyze_valid_resume_and_flow(client, sample_docx: Path, sample_jd_text: str):
    # 1. Test /api/analyze with valid sample resume
    with open(sample_docx, "rb") as f:
        file_bytes = f.read()

    data = {
        "resume": (io.BytesIO(file_bytes), "sample_resume.docx"),
        "job_description": sample_jd_text,
    }
    analyze_resp = client.post(
        "/api/analyze",
        data=data,
        content_type="multipart/form-data",
    )
    assert analyze_resp.status_code == 200
    analyze_data = analyze_resp.get_json()

    assert "session_id" in analyze_data
    assert "explicitly_matched" in analyze_data
    assert "questions" in analyze_data

    session_id = analyze_data["session_id"]
    assert len(analyze_data["explicitly_matched"]) > 0

    # 2. Test /api/answer
    if analyze_data["questions"]:
        question_to_answer = analyze_data["questions"][0]
        missing_skill = question_to_answer["missing_skill"]
        option = question_to_answer["options"][0]

        answer_resp = client.post(
            "/api/answer",
            json={
                "session_id": session_id,
                "missing_skill": missing_skill,
                "selected_option": option,
            },
        )
        assert answer_resp.status_code == 200
        answer_data = answer_resp.get_json()
        assert answer_data["status"] == "success"
        assert "remaining_questions" in answer_data

    # Test /api/answer with invalid session_id
    bad_answer_resp = client.post(
        "/api/answer",
        json={
            "session_id": "invalid-session-uuid",
            "missing_skill": "Distributed Systems",
            "selected_option": "Implemented it myself",
        },
    )
    assert bad_answer_resp.status_code == 404

    # 3. Test /api/report/<session_id>
    report_resp = client.get(f"/api/report/{session_id}")
    assert report_resp.status_code == 200
    report_data = report_resp.get_json()

    assert "fit_summary" in report_data
    assert "skills_breakdown" in report_data
    assert "suggested_rewrites" in report_data
    assert "fit_percentage" in report_data["fit_summary"]

    # Test /api/report with invalid session_id
    bad_report_resp = client.get("/api/report/nonexistent-session")
    assert bad_report_resp.status_code == 404


def test_api_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["service"] == "SkillGraph API"
    assert data["status"] == "operational"
    assert "health" in data
