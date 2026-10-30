# SkillGraph: Explainable Skill Inference & Resume Matching

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/Ashwin-R05/Skillgraph---NLP/actions/workflows/ci.yml/badge.svg)](https://github.com/Ashwin-R05/Skillgraph---NLP/actions/workflows/ci.yml)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React 19](https://img.shields.io/badge/React-19.x-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![spaCy](https://img.shields.io/badge/spaCy-en__core__web__sm-09A3D5?style=flat&logo=spacy&logoColor=white)](https://spacy.io/)
[![Sentence-Transformers](https://img.shields.io/badge/Sentence--Transformers-all--MiniLM--L6--v2-FFA116?style=flat)](https://www.sbert.net/)
[![NetworkX](https://img.shields.io/badge/NetworkX-DiGraph-blueviolet?style=flat)](https://networkx.org/)

**SkillGraph** is an NLP pipeline that extracts explicit skills from resumes, infers unstated (implicit) skills required by a job description using a hybrid knowledge graph and semantic embeddings, and generates grounded resume bullet suggestions through active candidate verification.

---

## 📌 Problem

Traditional keyword-matching Applicant Tracking Systems (ATS) evaluate candidate fit using literal string matching. If a job description asks for `REST API` and `Distributed Systems`, a candidate who wrote `FastAPI` and `Microservices` may be flagged as lacking core qualifications. 

Conversely, delegating this task entirely to generative Large Language Models (LLMs) presents trade-offs in recruiting:
1. **Hallucination Risk**: Unconstrained LLMs often fabricate achievements, metrics, or technologies not present in the original resume.
2. **Privacy Concerns**: Uploading candidate resumes and private job descriptions to commercial cloud APIs transmits personally identifiable information (PII).
3. **Non-Determinism**: LLM outputs can vary across runs, making consistent candidate scoring difficult to audit.

SkillGraph investigates a lightweight, local alternative: combining a curated domain graph prior with on-device sentence embeddings to infer implied competencies with traceable provenance.

---

## 🏗️ Architecture & Pipeline Overview

```mermaid
flowchart TD
    subgraph UI [Frontend - React + Vite]
        U1[1. Upload Resume & JD] -->|POST /api/analyze| API1[/api/analyze]
        U2[2. Verification Questions] -->|POST /api/answer| API2[/api/answer]
        U3[3. Candidate Fit Report & Rewrites] -->|GET /api/report/:id| API3[/api/report/:id]
    end

    subgraph BE [Backend Flask Pipeline - server.py]
        API1 --> S1[Stage 1: Parsing & Segmentation]
        
        subgraph Stage1 [Stage 1: skillgraph/parser.py]
            S1 --> S1_PARSE[pdfplumber / python-docx]
            S1_PARSE --> S1_CLN[Regex Noise & Section Header Stripping]
            S1_CLN --> S1_SEG[spaCy Sentence & Bullet Segmentation]
        end

        S1_SEG --> S2[Stage 2: Explicit Extraction]
        
        subgraph Stage2 [Stage 2: skillgraph/extractor.py]
            S2 --> S2_DICT[(skill_dictionary.json\n68 Canonical Skills)]
            S2_DICT --> S2_MTCH[Greedy Longest-Phrase Regex Matching]
            S2_MTCH --> S2_PROV[Record Statement-Level Provenance]
        end

        S2_PROV --> S3[Stage 3: Inference Engine]
        
        subgraph Stage3 [Stage 3: skillgraph/inference.py]
            S3 --> S3_DIFF[Identify Missing JD Skills]
            S3_DIFF --> S3_GRAPH[(skill_graph.json\n64 Directed Edges)]
            S3_DIFF --> S3_SBERT[Sentence-BERT Embeddings\nall-MiniLM-L6-v2]
            S3_GRAPH & S3_SBERT --> S3_FORM[Confidence Score Calculation:\n0.5 * Edge_Weight + 0.5 * Cosine_Sim]
            S3_FORM --> S3_CLS{Confidence Threshold}
            S3_CLS -->|> 74%| HIGH[HIGH_CONFIDENCE\nInferred directly]
            S3_CLS -->|40% to 74%| NV[NEEDS_VERIFICATION\nFlagged for Stage 4]
            S3_CLS -->|< 40%| GAP[SKILL_GAP\nGenuine Gap]
        end

        NV --> S4[Stage 4: Clarifying Questions]
        
        subgraph Stage4 [Stage 4: skillgraph/verifier.py]
            S4 --> S4_TMPL[(question_templates.json)]
            S4_TMPL --> S4_GEN[Generate Contextual Questions]
            S4_GEN --> API1
            API2 --> S4_RESP[Update Inference:\nCONFIRMED / PARTIAL / GAP]
        end

        S4_RESP & HIGH & GAP --> S5[Stage 5: Report & Rewriting]
        
        subgraph Stage5 [Stage 5: skillgraph/reporter.py]
            S5 --> S5_SCORE[Calculate Weighted Fit %]
            S5_SCORE --> S5_SLOT[Grounded Slot-Filling Rewrites]
            S5_SLOT --> API3
        end
    end

    API3 --> U3
```

---

## 🔬 How the Pipeline Works

1. **Stage 1: Parsing & Segmentation (`skillgraph/parser.py`)**
   - Parses `.docx` and `.pdf` files.
   - Cleans formatting artifacts and splits resumes into discrete, verifiable statement units using line boundaries and spaCy sentence segmentation.

2. **Stage 2: Explicit Extraction (`skillgraph/extractor.py`)**
   - Matches candidate statements against a curated dictionary (`skill_dictionary.json`, 68 skills with aliases).
   - Preserves exact statement-level provenance (recording which sentence evidenced each skill).

3. **Stage 3: Hybrid Inference Engine (`skillgraph/inference.py`)**
   - Determines which required job skills are absent from explicit resume text.
   - Finds candidate skills in a directed skill graph (`skill_graph.json`, 64 edges).
   - Computes dense cosine similarity between the candidate's actual resume statement and the missing skill using a local Sentence-BERT model (`all-MiniLM-L6-v2`).
   - Blends graph and semantic evidence:
     $$\text{Confidence} = \left( 0.50 \times w_{\text{graph}} + 0.50 \times \text{sim}_{\text{SBERT}} \right) \times 100$$
   - Categorizes outcomes into `HIGH_CONFIDENCE` ($>74\%$), `NEEDS_VERIFICATION` ($40\%\text{--}74\%$), or `SKILL_GAP` ($<40\%$).

4. **Stage 4: Clarifying Verification (`skillgraph/verifier.py`)**
   - Generates multiple-choice verification questions for borderline skills (`NEEDS_VERIFICATION`).
   - Translates user responses into confirmed (`CONFIRMED`), partially confirmed (`PARTIALLY_CONFIRMED`), or unverified gap states.

5. **Stage 5: Report Generation & Constrained Rewriting (`skillgraph/reporter.py`)**
   - Calculates candidate match percentage using weighted categories (explicit: 1.0, confirmed: 1.0, high-confidence: 0.85, partial: 0.5).
   - Produces suggested bullet rewrites using deterministic slot-filling on the candidate's original text, explicitly preventing hallucinated metrics or fabricated employers.

---

## ⚖️ Design Decisions: Deterministic Pipeline vs. Generative LLMs

SkillGraph deliberately uses a local, deterministic pipeline (graph prior + sentence embeddings + template slot-filling) rather than prompting a large language model. This reflects an engineering trade-off:

| Dimension | SkillGraph (Graph + SBERT + Templates) | Commercial Generative LLM |
| :--- | :--- | :--- |
| **Data Privacy** | Runs 100% locally on CPU. No resume text or PII leaves the host machine. | Sends resume text, contact details, and proprietary JDs to third-party APIs. |
| **Reproducibility** | Deterministic outputs. Identical inputs yield identical confidence scores and recommendations. | Non-deterministic sampling; results may drift across model versions or temperatures. |
| **Inference Cost & Speed** | Runs on commodity hardware in under 2 seconds. Zero API costs. | Recurring API costs per token; latency depends on cloud network and model load. |
| **Grounding & Provenance** | Every inference cites graph weight, cosine similarity, and original bullet line. Rewrites cannot invent facts. | High fluency, but vulnerable to subtle hallucinations (e.g. inventing team sizes, metrics, or tools). |
| **Coverage & Flexibility** | Limited to the curated vocabulary (68 skills, 64 edges). Requires manual graph maintenance. | Broad real-world knowledge across arbitrary industries and skills without manual ontology curation. |

SkillGraph does not claim to surpass LLMs in language fluency or broad knowledge; rather, it offers a bounded, privacy-safe, and explainable alternative for domain-constrained screening.

---

## 📊 Evaluation & Component Ablation

The system was evaluated against `eval_dataset.json`, a dataset of **18 test cases** comprising **60 labeled skill instances** across software engineering, data, and QA domains, hand-labeled by the author.

To measure the contribution of each component, we performed an ablation comparing:
- **(a) Explicit Only**: Keyword matching without inference.
- **(b) Graph-Only**: Graph edge weights only ($w_{\text{graph}} \ge 0.40$), ignoring statement text.
- **(c) SBERT-Only**: Semantic similarity only ($\text{cosine similarity} \ge 0.25$), ignoring graph edges.
- **(d) Hybrid (SkillGraph)**: Current system ($0.50 \cdot w_{\text{graph}} + 0.50 \cdot \text{sim}_{\text{SBERT}} \ge 40\%$).

### Empirical Ablation Results

| Method | Precision | Recall | F1-Score | False Positive Rate (Gaps) | Overall Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **(a) Explicit Only** | 0.0%* | 0.0% | 0.0% | **0.0%** | 71.7% |
| **(b) Graph-Only** | 84.2% | **94.1%** | 88.9% | 15.0% | 93.3% |
| **(c) SBERT-Only** | 80.0% | 70.6% | 75.0% | 15.0% | 86.7% |
| **(d) Hybrid (SkillGraph)** | **94.1%** | **94.1%** | **94.1%** | **5.0%** | **96.7%** |

*\*Explicit matching does not predict implicit skills, yielding 0 true positives for SHOULD_INFER.*

### Key Observations
1. **Graph Alone Over-Infers**: While the graph prior captures strong relationships (94.1% recall), it has a 15.0% false-positive rate on gaps because it cannot check whether the resume context actually supports the implied skill.
2. **SBERT Alone Suffers from Semantic Drift**: Sentence-BERT cosine similarity alone (70.6% recall, 15.0% FPR) lacks domain structure and struggles to distinguish adjacent technologies without graph boundaries.
3. **Hybrid Complementarity**: Combining the graph prior with SBERT contextual confirmation reduces the gap false-positive rate to **5.0%** (1 error in 20 gaps) while maintaining **94.1% recall and precision**.

See [`evaluation_results.md`](file:///mnt/Data/NLP/project/evaluation_results.md) for individual case breakdowns and detailed metric logs.

---

## ⚠️ Limitations

1. **Small Hand-Curated Graph**: The graph currently contains 68 skills and 64 directed edges. It covers common backend, frontend, data, and cloud technologies, but does not cover niche stacks or broad enterprise domains.
2. **1-Hop Traversal Only**: The inference engine only evaluates direct predecessors in the graph. It does not perform multi-hop graph traversal (e.g. `spaCy` $\to$ `NLP` $\to$ `Machine Learning` failed in Case 15 because there is no direct `spaCy` $\to$ `Machine Learning` edge).
3. **Small Self-Labeled Evaluation Set**: The evaluation dataset contains 18 cases and 60 labeled skills created by the author. It serves as an empirical sanity check, not a statistically exhaustive industry benchmark.
4. **Synthetic Test Data**: The evaluation was performed on clean, synthetic resume statements rather than noisy real-world documents with complex multi-column layouts, OCR artifacts, or non-standard styling.
5. **English Language Only**: Both the skill gazetteer and the spaCy parsing pipeline (`en_core_web_sm`) are English-only.
6. **Self-Reporting Verification Dependency**: The accuracy of Stage 5 rewrites depends on honest candidate responses during Stage 4 disambiguation.

---

## 🛠️ Tech Stack

- **Core Runtime**: Python 3.10+
- **NLP & Embeddings**: spaCy (`en_core_web_sm`), Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Graph Modeling**: NetworkX (`DiGraph`)
- **Document Ingestion**: `pdfplumber`, `python-docx`
- **Backend API**: Flask 3.x, Flask-CORS, Flask-Limiter
- **Testing**: pytest, GitHub Actions CI
- **Frontend**: React 19, Vite, Tailwind CSS

---

## 🌐 API Reference

| Method | Endpoint | Request Payload | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | None | Returns API operational status. |
| `POST` | `/api/analyze` | Multipart Form: `resume` (file, max 5 MB) + `job_description` (text) | Runs Stages 1–3, creates in-memory session, returns matched skills and clarifying questions. |
| `POST` | `/api/answer` | JSON: `{"session_id": "...", "missing_skill": "...", "selected_option": "..."}` | Updates inference status via Stage 4 and returns remaining question count. |
| `GET` | `/api/report/<session_id>` | URL Param: `session_id` | Compiles Stage 5 report and returns match breakdown and rewrite suggestions. |
| `POST` | `/api/bulk-analyze` | Multipart Form: `resumes` (multiple files) + `job_description` (text) | Sequentially runs multiple resumes and returns ranked candidates. |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm

### 2. Backend Setup

```bash
# Clone the repository
git clone https://github.com/Ashwin-R05/Skillgraph---NLP.git
cd Skillgraph---NLP

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Running the Application

Open two terminals:

**Terminal 1 (Backend API):**
```bash
source .venv/bin/activate
python server.py
# Runs on http://127.0.0.1:5000
```

**Terminal 2 (Frontend Development Server):**
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

### 5. Running Tests & Evaluation

```bash
# Run automated pytest suite
pytest -v tests/

# Run the 4-way ablation evaluation benchmark
python run_evaluation.py
```
