# SkillGraph — Stage 7: Inference Engine Evaluation Report

## 1. Executive Summary

This evaluation measures the empirical performance of the Stage 3 Inference Engine on a hand-curated test dataset of 18 realistic resume/job-description scenarios comprising 60 required skills.

The evaluation benchmarks whether the hybrid graph-semantic engine accurately:
1. Recommends plausible candidate skills for inference (**Precision & Recall**).
2. Refrains from over-inferring unrelated skills (**False Positive Rate on Genuine Gaps**).

> **Academic Limitation Note**: This evaluation is conducted on a small, hand-labeled synthetic dataset (18 cases, 60 skill targets) designed as a rigorous empirical sanity check and viva defense asset, rather than an exhaustive multi-thousand benchmark. No graph weights or model hyperparameters were artificially tuned to inflate these figures.

---

## 2. Key Performance Metrics

| Metric | Score | Interpretation |
| :--- | :--- | :--- |
| **Inference Precision** | **94.1%** | Of all skills the engine proposed to infer, 94.1% were genuine, justifiable inferences according to human judges. |
| **Inference Recall** | **94.1%** | The engine successfully surfaced 94.1% of the implicit skills that human judges expected. |
| **Inference F1-Score** | **94.1%** | Harmonic mean of precision and recall. |
| **False Positive Rate on Gaps** | **5.0%** | Rate at which genuine skill gaps were mistakenly inferred (1 out of 20 gaps). |
| **Overall Classification Accuracy** | **96.7%** | Accuracy across all three classes (EXPLICIT, SHOULD_INFER, GENUINE_GAP). |

---

## 3. Evaluation Breakdown & Error Analysis

- **Total Test Cases**: 18
- **Total Skills Evaluated**: 60
- **Correct Classifications**: 58
- **Total Misclassifications**: 2

### Misclassified Cases

| Case ID | Skill | Expected Label | Predicted Label | Reason for Discrepancy |
| :--- | :--- | :--- | :--- | :--- |
| `case_11_sql_databases` | **MySQL** | `GENUINE_GAP` | `SHOULD_INFER` | Graph prior or semantic overlap caused engine to infer a skill human judge deemed distinct. |
| `case_15_nlp_spacy` | **Machine Learning** | `SHOULD_INFER` | `GENUINE_GAP` | Graph weight or semantic similarity fell below verification threshold (conservative inference). |

---

## 4. Discussion & Viva Takeaways

1. **Conservative Inference Design**:
   The engine demonstrates high precision (94.1%) and a low false-positive rate on genuine gaps (5.0%). In recruitment automation, false positives are significantly more damaging than false negatives because falsely attributing a skill undermines recruiter trust. The low FPR confirms the engine avoids reckless over-inferencing.

2. **Source of Missed Inferences (Recall 94.1%)**:
   Where the engine labeled a skill as `GENUINE_GAP` instead of `SHOULD_INFER`, the cause is typically either:
   - The absence of a direct directed edge in `skill_graph.json`, or
   - Combined confidence falling slightly below the 40% threshold (`LOW_THRESHOLD = 40`) when semantic similarity between short bullet text and the skill name is moderate.

3. **Stage 4 Verification Safety Net**:
   Crucially, any inference flagged by Stage 3 with confidence between 40% and 85% is routed to Stage 4 clarifying questions (`NEEDS_VERIFICATION`), meaning candidates must self-verify before the skill is confirmed. This multi-stage architecture further protects real-world users from inference errors.
