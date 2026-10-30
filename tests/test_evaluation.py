from __future__ import annotations

import json
from pathlib import Path
from run_evaluation import (
    run_explicit_only_on_case,
    compute_metrics,
)


def test_eval_dataset_integrity():
    eval_path = Path(__file__).parent.parent / "eval_dataset.json"
    assert eval_path.exists()
    with open(eval_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    assert len(cases) == 18
    valid_labels = {"EXPLICIT", "SHOULD_INFER", "GENUINE_GAP"}

    total_skills = 0
    for case in cases:
        assert "id" in case
        assert "resume_statements" in case
        assert "job_description" in case
        assert "ground_truth" in case
        for skill, label in case["ground_truth"].items():
            assert label in valid_labels
            total_skills += 1

    assert total_skills == 60


def test_explicit_baseline_metrics(skill_dict):
    eval_path = Path(__file__).parent.parent / "eval_dataset.json"
    with open(eval_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    ground_truths = {c["id"]: c["ground_truth"] for c in cases}
    preds_explicit = {
        c["id"]: run_explicit_only_on_case(c, skill_dict)
        for c in cases
    }
    metrics = compute_metrics(preds_explicit, ground_truths)["metrics"]

    # Explicit matching cannot infer implicit skills
    assert metrics["recall"] == 0.0
    assert metrics["precision"] == 0.0
    assert metrics["false_positive_rate_on_gaps"] == 0.0
