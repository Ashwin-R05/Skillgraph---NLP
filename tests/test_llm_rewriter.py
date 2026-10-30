from __future__ import annotations

from skillgraph.llm_rewriter import generate_llm_rewrite, verify_grounding
from skillgraph.reporter import generate_rewrite


def test_llm_rewriter_default_fallback():
    # Without an API key, generate_llm_rewrite returns None and falls back to deterministic slot-filling
    inference = {
        "missing_skill": "Distributed Systems",
        "matched_resume_skill": "Microservices",
        "matched_statement": "Designed and implemented a microservices architecture using Python/FastAPI, reducing API latency by 35%.",
        "classification": "CONFIRMED",
        "selected_option": "Implemented it myself",
    }

    # Should safely return None without error
    res_none = generate_llm_rewrite(inference, api_key=None)
    assert res_none is None

    # generate_rewrite with use_llm=True but no key should return deterministic rewrite
    res_det = generate_rewrite(inference, use_llm=True, llm_api_key=None)
    assert "distributed" in res_det.lower()
    assert "35%" in res_det


def test_verify_grounding_clean():
    original = "Designed a microservices architecture using Python/FastAPI, reducing API latency by 35%."
    good_rewrite = "Architected distributed microservices systems using Python/FastAPI, reducing API latency by 35%."

    check = verify_grounding(original, good_rewrite, target_skill="Distributed Systems")
    assert check["is_grounded"] is True
    assert len(check["hallucinated_numbers"]) == 0


def test_verify_grounding_detects_hallucinations():
    original = "Designed a microservices architecture using Python/FastAPI, reducing API latency by 35%."
    hallucinated_rewrite = "Architected distributed microservices systems using Python/FastAPI, reducing API latency by 50% and saving $2M annually."

    check = verify_grounding(original, hallucinated_rewrite, target_skill="Distributed Systems")
    assert check["is_grounded"] is False
    assert any(n in check["hallucinated_numbers"] for n in ["50%", "2m"])
