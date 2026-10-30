from __future__ import annotations

from skillgraph.verifier import (
    load_question_templates,
    initialize_verification_status,
    generate_all_questions,
    apply_response,
)


def test_question_templates_structure(question_templates: list):
    assert isinstance(question_templates, list)
    assert len(question_templates) > 0
    # Every template should define id, template, and options
    for item in question_templates:
        assert isinstance(item, dict)
        assert "template" in item
        assert "options" in item
        assert isinstance(item["options"], list)


def test_initialize_verification_status():
    raw_inferences = [
        {"missing_skill": "Distributed Systems", "classification": "NEEDS_VERIFICATION"},
        {"missing_skill": "GCP", "classification": "SKILL_GAP"},
    ]
    initialized = initialize_verification_status(raw_inferences)
    assert len(initialized) == 2
    for item in initialized:
        assert item.get("verified") is False


def test_generate_all_questions(question_templates):
    inferences = [
        {
            "missing_skill": "Distributed Systems",
            "matched_resume_skill": "Microservices",
            "matched_statement": "Designed microservices",
            "classification": "NEEDS_VERIFICATION",
            "verified": False,
        },
        {
            "missing_skill": "GCP",
            "matched_resume_skill": "AWS",
            "matched_statement": "AWS certified",
            "classification": "SKILL_GAP",
            "verified": False,
        },
    ]

    questions = generate_all_questions(inferences, question_templates)
    # Only NEEDS_VERIFICATION inferences should trigger questions
    assert len(questions) == 1
    assert questions[0]["missing_skill"] == "Distributed Systems"
    assert "question" in questions[0]
    assert len(questions[0]["options"]) > 0


def test_apply_response():
    inference = {
        "missing_skill": "Distributed Systems",
        "matched_resume_skill": "Microservices",
        "matched_statement": "Designed microservices architecture",
        "classification": "NEEDS_VERIFICATION",
        "verified": False,
    }

    # 1. Candidate implemented it themselves -> CONFIRMED
    res_confirmed = apply_response(inference, "Implemented it myself")
    assert res_confirmed["classification"] == "CONFIRMED"
    assert res_confirmed["verified"] is True
    assert res_confirmed["selected_option"] == "Implemented it myself"

    # 2. Hands-on -> CONFIRMED
    res_handson = apply_response(inference, "Hands-on")
    assert res_handson["classification"] == "CONFIRMED"
    assert res_handson["verified"] is True

    # 3. Used a library/tool -> PARTIALLY_CONFIRMED
    res_partial = apply_response(inference, "Used a library/tool")
    assert res_partial["classification"] == "PARTIALLY_CONFIRMED"
    assert res_partial["verified"] is True

    # 4. Part of a framework -> PARTIALLY_CONFIRMED
    res_framework = apply_response(inference, "Part of a framework")
    assert res_framework["classification"] == "PARTIALLY_CONFIRMED"
    assert res_framework["verified"] is True

    # 5. Not sure -> SKILL_GAP
    res_gap = apply_response(inference, "Not sure")
    assert res_gap["classification"] == "SKILL_GAP"
    assert res_gap["verified"] is True
