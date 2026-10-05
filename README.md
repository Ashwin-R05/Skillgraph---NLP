# SkillGraph — Explainable Implicit Skill Inference & Resume Evaluation

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React 19](https://img.shields.io/badge/React-19.x-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.x-646CFF?style=flat&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4.x-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![spaCy](https://img.shields.io/badge/spaCy-en__core__web__sm-09A3D5?style=flat&logo=spacy&logoColor=white)](https://spacy.io/)
[![Sentence-Transformers](https://img.shields.io/badge/Sentence--Transformers-all--MiniLM--L6--v2-FFA116?style=flat)](https://www.sbert.net/)
[![NetworkX](https://img.shields.io/badge/NetworkX-DiGraph-blueviolet?style=flat)](https://networkx.org/)

**SkillGraph** is an explainable Natural Language Processing (NLP) system designed to solve a fundamental flaw in automated talent screening: **candidates rarely enumerate every foundational tool, protocol, or concept they use, yet keyword-matching Applicant Tracking Systems (ATS) disqualify them for unstated implicit competencies.**

Rather than delegating candidate evaluation to ungrounded, hallucination-prone generative LLMs, SkillGraph combines:
1. **Curated Skill Gazetteer & Alias Matching**: Extracts explicit skills with sentence-level provenance.
2. **Hybrid Graph Traversal & Local Sentence-BERT**: Infers unstated skills using domain graph priors ($w_{\text{edge}}$) and contextual semantic embeddings ($\text{sim}_{\text{BERT}}$).
3. **Active Candidate Disambiguation**: Solicits targeted human clarification for borderline inferences to prevent false positives.
4. **Constrained Slot-Filling Rewriting**: Proposes verifiable resume bullet revisions without fabricating achievements, metrics, or tools.
5. **Research-Grade Web Application**: Features an academic-prestige React frontend and a hardened Flask REST backend.

---

## 🛠️ Technology Stack

SkillGraph is engineered with separation of concerns between an offline-capable NLP computation engine and an institutional-grade reactive web interface.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SKILLGRAPH SYSTEM STACK                         │
├───────────────────────────────────┬────────────────────────────────────┤
│           BACKEND STACK           │           FRONTEND STACK           │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Python 3.10+ (Core Runtime)     │ • React 19 (Functional Components) │
│ • Flask (RESTful Microframework)  │ • Vite 8 (HMR & Production Bundle) │
│ • spaCy (en_core_web_sm)          │ • Tailwind CSS v4 (Design Engine)  │
│ • Sentence-Transformers (Local)   │ • Instrument Serif & Plus Jakarta  │
│ • NetworkX (Directed Graph)       │ • JetBrains Mono (Math/Code Font)  │
│ • pdfplumber & python-docx        │ • Native Web Clipboard & Print API │
│ • Flask-Limiter & Flask-CORS      │ • Zero External UI Library Bloat   │
└───────────────────────────────────┴────────────────────────────────────┘
```

### 1. Backend Technologies
- **Python 3.10+**: Core language for pipeline modules, tensor operations, and file processing.
- **Flask**: Lightweight WSGI microframework exposing REST endpoints with session state management.
- **spaCy (`en_core_web_sm`)**: Used in Stage 1 for sentence segmentation and in Stage 2 for entity cross-referencing. Runs locally.
- **Sentence-Transformers (`all-MiniLM-L6-v2`)**: Generates 384-dimensional dense semantic embeddings to measure cosine similarity between resume statements and missing skill names. Runs completely on-device without cloud API dependencies.
- **NetworkX**: In-memory directed graph (`DiGraph`) modeling prerequisite and co-occurrence relationships across 68 technical competencies and 64 curated edges.
- **`pdfplumber` & `python-docx`**: Native extractors for PDF and DOCX document streams with structural cleanup and boundary repair.
- **`Flask-Limiter`**: In-memory rate limiting (`10/min` on heavy NLP analysis, `60/min` on interaction endpoints) protecting against compute starvation.
- **Security Hardening**: Built-in magic bytes validation (`%PDF-`, `PK\x03\x04`), 5 MB request size bounds (`MAX_CONTENT_LENGTH`), DOCX decompression bomb defense, and strict sanitization headers (`CSP`, `X-Frame-Options`, `nosniff`).

### 2. Frontend Technologies
- **React 19**: Reactive single-page application driving the 3-stage user journey (Document Ingestion $\rightarrow$ Active Disambiguation $\rightarrow$ Fit Dossier & Rewrite Studio).
- **Vite 8**: Modern build pipeline with sub-second hot module replacement and production tree-shaking producing a 78 KB gzipped bundle.
- **Tailwind CSS v4**: Utility-first design system utilizing `@theme` tokens for academic aesthetics, glassmorphism, responsive data grids, and glowing accent borders.
- **Academic Typography**:
  - *Display Serif*: **Instrument Serif** for prestigious editorial titles.
  - *Interface Sans*: **Plus Jakarta Sans** for readable data matrices, badges, and controls.
  - *Monospace*: **JetBrains Mono** for algebraic formulas, confidence scores, and code tokens.
- **Native Browser Integrations**:
  - Drag-and-drop file upload with real-time size and format inspection.
  - Interactive keyboard shortcuts (`[1]`, `[2]`, `[3]`) for rapid interview navigation.
  - One-click copy-to-clipboard for suggested revisions.
  - Full print media stylesheet (`@media print`) for compiling physical paper dossiers or PDF exports.

---

## 🔄 End-to-End Project Workflow

The following diagram illustrates how raw documents flow through SkillGraph's 5 core pipeline stages, web API, and user interface:

```mermaid
flowchart TD
    subgraph UI [Frontend User Interface - React + Vite]
        U1[1. Upload Resume & Input JD] -->|POST multipart/form-data| API1[/api/analyze]
        U2[2. Active Verification Interview] -->|POST JSON choice| API2[/api/answer]
        U3[3. Candidate Fit Dossier & Rewrites] -->|GET report| API3[/api/report/:id]
    end

    subgraph BE [Backend Flask Pipeline - server.py]
        API1 --> S1[Stage 1: Parsing & Segmentation]
        
        subgraph Stage1 [Stage 1: skillgraph/parser.py]
            S1 --> S1_PDF[pdfplumber / python-docx]
            S1_PDF --> S1_SEC[Security Check: Magic Bytes & Zip Bomb Defense]
            S1_SEC --> S1_CLN[Regex Noise & Header Stripping]
            S1_CLN --> S1_SEG[spaCy Bullet-Level Statement Segmentation]
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
            S3_GRAPH & S3_SBERT --> S3_FORM[Compute Confidence:\n0.5 * Edge_Weight + 0.5 * Cosine_Sim]
            S3_FORM --> S3_CLS{Confidence Threshold}
            S3_CLS -->|> 85%| HIGH[HIGH_CONFIDENCE\nAuto-Accepted]
            S3_CLS -->|40% to 85%| NV[NEEDS_VERIFICATION\nFlagged for Stage 4]
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
            S5_SCORE --> S5_SLOT[Deterministic Slot-Filling Rewrites]
            S5_SLOT --> API3
        end
    end

    API3 --> U3
```

---

## 🔬 Detailed Pipeline Stages

### Stage 1: Parsing & Segmentation (`skillgraph/parser.py`)
- **File Validation**: Inspects magic numbers (`%PDF-` for PDF, `PK\x03\x04` for DOCX) and validates zip entries to defend against decompression bombs (max uncompressed size: 25 MB, max compression ratio: 100:1).
- **Layout Repair**: Normalizes carriage returns, collapses multiple newlines, and rejoins lines split mid-sentence by multi-column PDF layouts.
- **Section & Noise Stripping**: Filters out resume section titles (e.g. `SUMMARY`, `EXPERIENCE`, `EDUCATION`, `SKILLS`) and decorative separator lines.
- **Statement Segmentation**: Splits resumes on author-intended line breaks, using spaCy sentence segmentation as a fallback for run-on paragraphs (> 200 characters).
- **Job Description Cleaning**: Normalizes job text into a clean block string (capped at 50,000 characters).

### Stage 2: Explicit Skill Extraction (`skillgraph/extractor.py`)
- **Ontology Gazetteer**: Loads `skillgraph/skill_dictionary.json` containing 68 canonical technical skills and hundreds of synonym aliases (e.g. `"golang"` $\rightarrow$ `"Go"`, `"drf"` $\rightarrow$ `"Django"`, `"k8s"` $\rightarrow$ `"Kubernetes"`).
- **Boundary-Aware Matching**: Performs greedy, longest-match-first regex phrase matching with word boundaries to prevent sub-string false alarms (e.g. preventing `"go"` from matching inside `"django"`).
- **Statement Provenance**: Retains the exact resume sentence in which each skill was identified:
  ```json
  {
    "skill": "FastAPI",
    "source_statement": "Designed and implemented a microservices architecture using Python/FastAPI and PostgreSQL, reducing API latency by 35%."
  }
  ```

### Stage 3: Inference Engine (`skillgraph/inference.py`)
Identifies which required skills are missing from the resume but likely possessed by the candidate based on related competencies:
- **Graph Traversal**: Queries the NetworkX directed graph (`skillgraph/skill_graph.json`) for predecessors pointing into the missing skill.
- **Contextual Semantic Similarity**: Computes the cosine similarity between the candidate's actual source statement and the missing skill name using Sentence-BERT (`all-MiniLM-L6-v2`).
- **Mathematical Confidence Formula**:
  $$\text{Confidence} = \left( 0.50 \cdot w_{\text{graph}} + 0.50 \cdot \text{sim}_{\text{SBERT}} \right) \times 100$$
- **Classification Rules**:
  - `HIGH_CONFIDENCE` ($\ge 85\%$): Strong graph relationship and semantic evidence.
  - `NEEDS_VERIFICATION` ($40\% \le \text{Confidence} < 85\%$): Plausible inference requiring human verification.
  - `SKILL_GAP` ($< 40\%$ or no graph predecessor): Genuine skill deficiency.
- **Explainable Reasoning**: Produces a plain-English explanation citing the specific resume statement, predecessor skill, edge weight, and cosine similarity.

### Stage 4: Question Generation & Verification (`skillgraph/verifier.py`)
- **Targeted Generation**: Questions are generated strictly for `NEEDS_VERIFICATION` items (skipping obvious matches and gaps).
- **Pre-Authored Templates**: Uses deterministic templates (`skillgraph/question_templates.json`) rather than generative LLMs.
- **Response Mapping**:
  - *"Implemented it myself"* / *"Hands-on"* $\rightarrow$ **`CONFIRMED`** (Weight: 1.0)
  - *"Used a library or tool"* / *"Part of a framework"* $\rightarrow$ **`PARTIALLY_CONFIRMED`** (Weight: 0.5)
  - *"Not sure"* $\rightarrow$ **`SKILL_GAP`** (Weight: 0.0)

### Stage 5: Report Compilation & Constrained Rewriting (`skillgraph/reporter.py`)
- **Weighted Fit Score**:
  $$\text{Fit Percentage} = \text{round}\left( \frac{N_{\text{explicit}} \cdot 1.0 + N_{\text{confirmed}} \cdot 1.0 + N_{\text{high\_unverified}} \cdot 0.85 + N_{\text{partial}} \cdot 0.5}{N_{\text{total\_required}}} \times 100 \right)$$
- **Academic Honesty in Rewriting**: Rewrites are performed using deterministic sentence slot-filling anchored directly to the candidate's original resume statement.
  - Confirmed skills highlight active implementation.
  - Partially confirmed skills transparently indicate tooling/framework exposure.
  - Zero hallucination of external metrics, companies, or tools.

### Stage 6: Integration & Web Application (`server.py` & `frontend/`)
- Connects Stages 1 through 5 into an interactive HTTP API server and React frontend.
- Provides session isolation, rate limiting, and an educational dark-mode UI with live metric gauges.

### Stage 7: Empirical Evaluation (`run_evaluation.py`)
- Independent evaluation harness testing the inference engine against `eval_dataset.json` (18 hand-labeled test cases, 60 skill targets).
- Measures Precision, Recall, F1-Score, and False Positive Rate on genuine gaps.

---

## 📊 Empirical Evaluation Results (Stage 7)

Tested against the hand-labeled benchmark dataset (`eval_dataset.json`):

| Evaluation Metric | Score | Explanation |
| :--- | :--- | :--- |
| **Total Test Cases** | **18** | Diverse coverage across Backend, Frontend, Data, ML, Cloud/DevOps, Security, and QA. |
| **Total Skills Evaluated** | **60** | Full set of required competencies evaluated across all scenarios. |
| **Inference Precision** | **94.1%** | 16 of 17 skills proposed for inference were genuine, justifiable competencies. |
| **Inference Recall** | **94.1%** | Successfully inferred 16 of 17 implicit competencies expected by human evaluators. |
| **Inference F1-Score** | **94.1%** | Harmonic mean of precision and recall. |
| **False Positive Rate on Gaps** | **5.0%** | Only 1 out of 20 genuine gaps was mistakenly flagged for verification. |
| **Overall Classification Accuracy** | **96.7%** | 58 of 60 skill classifications matched ground truth exactly. |

---

## 🌐 API Reference (Stage 6)

| Method | Endpoint | Request Payload | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | None | Returns API service operational status. |
| `POST` | `/api/analyze` | Multipart Form: `resume` (file) + `job_description` (text) | Runs Stages 1–3, creates in-memory session, returns matched skills & clarifying questions. |
| `POST` | `/api/answer` | JSON: `{"session_id": "...", "missing_skill": "...", "selected_option": "..."}` | Updates inference status via Stage 4 and returns remaining question count. |
| `GET` | `/api/report/<session_id>` | URL Param: `session_id` | Compiles Stage 5 report and returns final fit breakdown and rewrite suggestions. |

---

## 📁 Repository File Structure

```
.
├── server.py                     # Stage 6: Hardened Flask API Backend
├── run_evaluation.py             # Stage 7: Evaluation Runner & Metrics Engine
├── eval_dataset.json             # Stage 7: 18 Hand-Labeled Ground-Truth Test Cases
├── evaluation_results.md         # Stage 7: Auto-Generated Academic Results Report
├── requirements.txt              # Backend Dependencies (Python)
├── samples/
│   └── sample_resume.docx        # Generated Benchmark Resume (Priya Sharma)
├── skillgraph/                   # Core Pipeline Package
│   ├── __init__.py
│   ├── parser.py                 # Stage 1: Document Ingestion, Security & Segmentation
│   ├── extractor.py              # Stage 2: Explicit Extraction with Provenance
│   ├── skill_dictionary.json     # 68 Canonical Skills with Multi-Variant Aliases
│   ├── inference.py              # Stage 3: NetworkX Graph Traversal & Local SBERT
│   ├── skill_graph.json          # Directed Skill Relationship Graph (64 Edges)
│   ├── verifier.py               # Stage 4: Question Generation & Verification
│   ├── question_templates.json   # Deterministic Clarifying Templates
│   └── reporter.py               # Stage 5: Fit Score Compilation & Slot-Filled Rewrites
├── frontend/                     # Stage 6: React + Vite + Tailwind CSS Frontend
│   ├── index.html                # HTML Entrypoint with Google Fonts
│   ├── vite.config.js            # Vite Configuration & Backend API Proxy
│   ├── package.json              # Frontend Dependencies & Scripts
│   ├── public/
│   │   └── sample_resume.docx    # 1-Click Evaluation Asset
│   └── src/
│       ├── main.jsx              # React DOM Root
│       ├── index.css             # Tailwind v4 Theme Tokens & Print Styles
│       └── App.jsx               # Complete 3-Screen Reactive UI
├── test_stage1.py                # Standalone Test for Stage 1
├── test_stage2.py                # Standalone Test for Stage 2
├── test_stage3.py                # Standalone Test for Stage 3
├── test_stage4.py                # Standalone Test for Stage 4
├── test_stage5.py                # Standalone Test for Full Pipeline (Stages 1–5)
└── README.md                     # Comprehensive Project Documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python**: Version 3.10 or higher.
- **Node.js**: Version 18 or higher (with `npm`).
- **Operating System**: Linux, macOS, or Windows (WSL recommended).

### 2. Backend Installation

```bash
# Clone the repository
git clone https://github.com/Ashwin-R05/Skillgraph---NLP.git
cd Skillgraph---NLP

# Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
pip install flask flask-cors flask-limiter

# Download the spaCy English pipeline
python -m spacy download en_core_web_sm
```

### 3. Frontend Installation

```bash
cd frontend
npm install
cd ..
```

### 4. Running the Complete System (Backend + Frontend)

Open two terminal tabs:

**Terminal 1 (Flask API Server):**
```bash
source .venv/bin/activate
python server.py
# Server starts on http://127.0.0.1:5000
```

**Terminal 2 (React Frontend):**
```bash
cd frontend
npm run dev
# Vite dev server starts on http://localhost:5173
```

Navigate to **`http://localhost:5173`** in your browser. You can click **"Load Benchmark Resume"** to test the complete workflow in one click!

### 5. Running Standalone CLI Tests

Each pipeline stage includes an independent CLI test script:

```bash
source .venv/bin/activate

python test_stage1.py     # Test Stage 1: Document Parsing & Segmentation
python test_stage2.py     # Test Stage 2: Explicit Skill Extraction
python test_stage3.py     # Test Stage 3: Inference Engine
python test_stage4.py     # Test Stage 4: Question Verification
python test_stage5.py     # Test Full Stage 1 to 5 Chain
python run_evaluation.py  # Test Stage 7: Empirical Evaluation Suite
```

---

## 🛡️ Academic Integrity & Privacy Principles

1. **Zero External API / LLM Dependencies**:
   - The entire pipeline runs 100% locally on CPU/GPU. No resume text, candidate names, or confidential job descriptions are ever sent to OpenAI, Anthropic, or external cloud services.
2. **Guaranteed Explainability**:
   - Every inferred skill is accompanied by an algebraic breakdown ($w_{\text{edge}}$, $\text{sim}_{\text{SBERT}}$) and cites the exact resume sentence that led to the conclusion.
3. **No Generative Hallucination**:
   - Resume bullet revisions use deterministic slot-filling on the candidate's existing statements, preventing the fabrication of unverified accomplishments or metrics.
4. **Active Disambiguation**:
   - Inferences between 40% and 85% confidence are not assumed true; they must be verified by the candidate, strictly bounding the false positive rate (5.0%).
