from __future__ import annotations

from skillgraph.reporter import (
    compile_report,
    generate_all_rewrites,
    build_final_output,
)


def test_compile_report_and_fit_score():
    stage4_output = {
        "explicitly_matched": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        "inferences": [
            {
                "missing_skill": "Distributed Systems",
                "classification": "CONFIRMED",
                "verified": True,
                "confidence": 75,
                "matched_resume_skill": "Microservices",
                "matched_statement": "Designed microservices architecture using Python/FastAPI.",
                "reasoning": "Microservices implies Distributed Systems",
            },
            {
                "missing_skill": "ETL",
                "classification": "PARTIALLY_CONFIRMED",
                "verified": True,
                "confidence": 60,
                "matched_resume_skill": "Apache Spark",
                "matched_statement": "Built Spark pipeline for processing event streams.",
                "reasoning": "Spark implies ETL",
            },
            {
                "missing_skill": "Kubernetes",
                "classification": "HIGH_CONFIDENCE",
                "verified": False,
                "confidence": 80,
                "matched_resume_skill": "Docker",
                "matched_statement": "Used Docker containers in staging and production.",
                "reasoning": "Docker related to Kubernetes",
            },
            {
                "missing_skill": "GCP",
                "classification": "SKILL_GAP",
                "verified": False,
                "confidence": 20,
                "matched_resume_skill": None,
                "matched_statement": "",
                "reasoning": "No evidence",
            },
        ],
    }

    report = compile_report(stage4_output)

    assert "fit_summary" in report
    assert "explicitly_present" in report
    assert "confirmed_by_inference" in report
    assert "partially_confirmed" in report
    assert "high_confidence_unverified" in report
    assert "genuine_gaps" in report

    summary = report["fit_summary"]
    # Total required = 4 explicit + 4 inferred = 8
    assert summary["total_required_skills"] == 8
    # Matched count = 4 explicit + 1 confirmed + 1 partial + 1 high_conf = 7
    assert summary["matched_count"] == 7

    assert len(report["explicitly_present"]) == 4
    assert len(report["confirmed_by_inference"]) == 1
    assert len(report["partially_confirmed"]) == 1
    assert len(report["high_confidence_unverified"]) == 1
    assert len(report["genuine_gaps"]) == 1


def test_generate_all_rewrites():
    report = {
        "explicitly_present": ["Python", "Docker"],
        "confirmed_by_inference": [
            {
                "missing_skill": "Distributed Systems",
                "matched_statement": "Designed and implemented a microservices architecture using Python/FastAPI, reducing API latency by 35%.",
                "matched_resume_skill": "Microservices",
                "selected_option": "Implemented it myself",
            }
        ],
        "partially_confirmed": [
            {
                "missing_skill": "ETL",
                "matched_statement": "Built real-time data pipelines with Apache Kafka and Spark Structured Streaming.",
                "matched_resume_skill": "Apache Spark",
                "selected_option": "Used a library/tool",
            }
        ],
        "high_confidence_unverified": [],
        "genuine_gaps": [{"missing_skill": "Rust"}],
        "fit_summary": {"total_required_skills": 5, "matched_count": 4, "fit_percentage": 80},
    }

    rewrites = generate_all_rewrites(report)
    assert isinstance(rewrites, list)
    assert len(rewrites) >= 1

    skills_rewritten = {rw["missing_skill"] for rw in rewrites}
    assert "Distributed Systems" in skills_rewritten
    # Gaps should never have rewrites fabricated
    assert "Rust" not in skills_rewritten

    for rw in rewrites:
        assert "original_statement" in rw
        assert "suggested_rewrite" in rw
        assert len(rw["suggested_rewrite"]) > 0


def test_build_final_output():
    report = {
        "explicitly_present": ["Python"],
        "confirmed_by_inference": [],
        "partially_confirmed": [],
        "high_confidence_unverified": [],
        "genuine_gaps": [],
        "fit_summary": {"total_required_skills": 1, "matched_count": 1, "fit_percentage": 100},
    }
    rewrites = []
    final = build_final_output(report, rewrites)
    assert "fit_summary" in final
    assert "skills_breakdown" in final
    assert "suggested_rewrites" in final
    assert final["suggested_rewrites"] == []
    assert final["skills_breakdown"]["explicitly_present"] == ["Python"]
