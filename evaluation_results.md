# SkillGraph — Evaluation Results & Ablation Analysis

## 1. Dataset & Methodology Transparency

> **Author Disclosure**: This evaluation is benchmarked on a compact, self-labeled dataset (`eval_dataset.json`) consisting of **18 test cases** and **60 labeled skill instances** created by the author. Every number presented here is reproducible and was directly produced by executing `python run_evaluation.py`.

### Ground Truth Breakdown
- **Explicit Skills**: 23 instances (skills explicitly stated in the candidate's resume)
- **Should Infer (Implicit Skills)**: 17 instances (skills absent from the text that a human technical interviewer expects the candidate to possess)
- **Genuine Gaps**: 20 instances (skills requested by the JD that the candidate has no demonstrable background in)
- **Total Skills Evaluated**: 60

---

## 2. Component Ablation Study

To evaluate the contribution of each layer in SkillGraph's architecture, we compare four approaches under identical test inputs:

1. **(a) Explicit Keyword Matching Only**: Traditional ATS keyword baseline without any inference layer.
2. **(b) Graph-Only Inference**: Uses hand-curated graph edge weights ($w_{graph} \ge 0.40$), ignoring candidate statement text.
3. **(c) Sentence-BERT-Only Inference**: Evaluates direct cosine semantic similarity between resume statements and missing skill names (calibrated threshold $\ge 0.25$), without topological graph constraints.
4. **(d) Current Hybrid Method (SkillGraph)**: Blends the curated graph prior with SBERT contextual embedding similarity:
   $$\text{Confidence} = (0.50 \times w_{graph} + 0.50 \times \text{sim}_{SBERT}) \times 100 \ge 40\%$$

### Ablation Comparison Table

| Method | Precision | Recall | F1-Score | False Positive Rate (Gaps) | Overall Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **(a) Explicit Only** | 0.0%* | 0.0% | 0.0% | **0.0%** | 71.7% |
| **(b) Graph-Only** | 84.2% | **94.1%** | 88.9% | 15.0% | 93.3% |
| **(c) SBERT-Only** | 80.0% | 70.6% | 75.0% | 15.0% | 86.7% |
| **(d) Hybrid (SkillGraph)** | **94.1%** | **94.1%** | **94.1%** | **5.0%** | **96.7%** |

*\*Explicit matching does not predict implicit skills, yielding 0 true positives for SHOULD_INFER.*

### Key Takeaways from Ablation
- **Why Graph Alone is Insufficient**: The graph prior identifies 16 of 17 inferable skills (Recall: 94.1%), but suffers from a **15.0% false-positive rate on genuine gaps** (e.g., inferring MySQL and MongoDB whenever PostgreSQL is present, regardless of context).
- **Why SBERT Alone is Insufficient**: Without structural graph priors, Sentence-BERT cosine similarity between generic bullet statements and isolated skill acronyms suffers from low semantic sharpness (F1: 75.0%), confusing adjacent technologies.
- **The Value of Hybrid Fusion**: Combining the knowledge graph prior with SBERT contextual confirmation reduces the false-positive rate from 15.0% down to **5.0%** while preserving top-tier recall (94.1%) and reaching an F1-score of **94.1%**.

---

## 3. Error Analysis on Actual System Outputs

On the 60 evaluated skill cases, the hybrid system made exactly **2 errors** (58 / 60 correct, 96.7% accuracy):

### 1. False Positive on Genuine Gap: `case_11_sql_databases`
- **Missing Skill**: `MySQL`
- **Expected Label**: `GENUINE_GAP` (The job description demanded dedicated MySQL DBA administration experience).
- **Predicted Label**: `SHOULD_INFER` (`NEEDS_VERIFICATION` with 40% confidence).
- **Root Cause**: The candidate's resume stated: *"Designed relational database schemas, normalized tables, and wrote complex queries in PostgreSQL."* The knowledge graph contains a directed edge from `PostgreSQL` to `MySQL` ($w=0.55$) representing general relational database knowledge transfer. Combined with SBERT similarity of 0.26, the hybrid confidence reached:
  $$(0.50 \times 0.55 + 0.50 \times 0.26) \times 100 = 40.5\% \approx 40\%$$
  Because 40% meets the threshold for `NEEDS_VERIFICATION`, the engine proposed verifying MySQL.
- **Mitigation in Pipeline**: While technically a false positive under binary classification, this output routes to a Stage 4 clarifying question. If the candidate answers *"Not sure"*, the pipeline immediately demotes MySQL to a genuine skill gap before the final report is compiled.

### 2. False Negative on Inferable Skill: `case_15_nlp_spacy`
- **Missing Skill**: `Machine Learning`
- **Expected Label**: `SHOULD_INFER`
- **Predicted Label**: `GENUINE_GAP` (Confidence: 0%)
- **Root Cause**: The candidate's resume described building NER pipelines using `spaCy`. In `skill_graph.json`, directed edges to `Machine Learning` exist from `PyTorch`, `TensorFlow`, `scikit-learn`, and `NLP`, but **no direct 1-hop edge exists from `spaCy` to `Machine Learning`**. Because the candidate did not explicitly write the letters "NLP" or "scikit-learn", the 1-hop graph search found zero predecessors, resulting in 0% confidence.
- **Mitigation in Pipeline**: Expand graph coverage or support 2-hop traversals (e.g. `spaCy` $\to$ `NLP` $\to$ `Machine Learning`).

---

## 4. How to Extend the Dataset (Recommendations for Future Labeling)

The current 18-case dataset is focused on web, data engineering, and backend roles. To benchmark SkillGraph for production or academic submission, the dataset should be expanded to 50–100 cases. 

### Recommended Scenarios to Hand-Label:
1. **Cloud & Platform Engineering**: Resumes with Terraform, Ansible, and CloudFormation targeting GCP/Azure roles (evaluating multi-cloud infrastructure inference).
2. **Mobile Development**: React Native and Flutter profiles applying for native iOS (Swift) / Android (Kotlin) positions.
3. **Data Science & ML Engineering**: Resumes focusing on Pandas, NumPy, and Scikit-Learn applying for Deep Learning/LLM roles requiring PyTorch and CUDA.
4. **Systems & Embedded Programming**: C/C++ developers applying for Rust systems roles.
5. **Security Engineering**: Pen-testing/OWASP backgrounds applying for DevSecOps/OAuth compliance roles.
