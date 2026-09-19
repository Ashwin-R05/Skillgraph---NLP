#!/usr/bin/env python3
"""
SkillGraph Stage 4 — Test Script

Runs Stage 1 → 2 → 3 on the sample resume, generates clarifying questions
for all NEEDS_VERIFICATION inferences, simulates a candidate answering one
of the questions, and applies the response to show the updated verification state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document

from skillgraph.parser import extract_resume_text, segment_resume, clean_jd_text
from skillgraph.extractor import (
    extract_resume_skills,
    extract_jd_skills,
    load_skill_dictionary,
)
from skillgraph.inference import (
    build_graph,
    load_skill_graph,
    load_sbert_model,
    run_inference,
)
from skillgraph.verifier import (
    load_question_templates,
    generate_all_questions,
    apply_response,
    initialize_verification_status,
)

# ── Sample resume & JD (standard project test data) ─────────────────

SAMPLE_RESUME_LINES = [
    ("Priya Sharma", True),
    ("priya.sharma@email.com | linkedin.com/in/priyasharma | github.com/priyaS", False),
    ("", False),
    ("SUMMARY", True),
    (
        "Full-stack engineer with 4+ years of experience building scalable "
        "web applications and data pipelines. Passionate about clean code, "
        "test-driven development, and mentoring junior developers.",
        False,
    ),
    ("", False),
    ("EXPERIENCE", True),
    ("Software Engineer II — Acme Corp, Bangalore (Jan 2022 – Present)", True),
    (
        "• Designed and implemented a microservices architecture using "
        "Python/FastAPI and PostgreSQL, reducing API latency by 35%.",
        False,
    ),
    (
        "• Built a real-time data pipeline with Apache Kafka and Spark "
        "Structured Streaming to process 2M+ events/day.",
        False,
    ),
    (
        "• Led a team of 3 engineers to deliver an internal analytics "
        "dashboard in React and D3.js, adopted by 150+ users.",
        False,
    ),
    (
        "• Wrote comprehensive unit and integration tests using pytest, "
        "achieving 92% code coverage.",
        False,
    ),
    ("", False),
    ("Software Engineer — StartupXYZ, Hyderabad (Jun 2020 – Dec 2021)", True),
    (
        "• Developed RESTful APIs in Django REST Framework serving 50k "
        "daily active users.",
        False,
    ),
    (
        "• Automated CI/CD pipelines with GitHub Actions and Docker, "
        "cutting deployment time from 45 min to 8 min.",
        False,
    ),
    (
        "• Integrated Elasticsearch for full-text search across 1.2M "
        "product listings, improving search speed by 60%.",
        False,
    ),
    ("", False),
    ("PROJECTS", True),
    ("SkillGraph (Personal Project)", True),
    (
        "• Building an NLP pipeline to infer implicit skills from resumes "
        "using spaCy, sentence transformers, and knowledge graphs.",
        False,
    ),
    ("", False),
    ("Open-source Contributor — Apache Airflow", True),
    (
        "• Fixed 12 bugs related to DAG scheduling and task retries; "
        "reviewed 30+ community pull requests.",
        False,
    ),
    ("", False),
    ("EDUCATION", True),
    ("B.Tech in Computer Science — IIT Hyderabad (2016 – 2020)", False),
    ("", False),
    ("SKILLS", True),
    (
        "Python, JavaScript, TypeScript, SQL, FastAPI, Django, React, "
        "Docker, Kubernetes, Kafka, Spark, PostgreSQL, Redis, Git",
        False,
    ),
    ("", False),
    ("CERTIFICATIONS", True),
    ("AWS Certified Solutions Architect – Associate (2023)", False),
    ("", False),
    ("---", False),
]

SAMPLE_JD = """\
Senior Backend Engineer — FinTech Startup (Remote)

About the role
We're looking for a Senior Backend Engineer to design,  build, and
maintain high-throughput financial systems.   You'll work closely with
the product team to ship features that handle millions of transactions
per day.

Responsibilities
- Architect and implement scalable backend services in Python
- Design event-driven systems using  message queues (Kafka, RabbitMQ)
- Own the full lifecycle of features from design to production
- Mentor junior engineers and conduct code reviews
- Collaborate with data engineering to build reliable ETL pipelines

Requirements
- 4+ years of backend engineering experience
- Strong proficiency in Python (FastAPI or Django)
- Experience with relational databases (PostgreSQL, MySQL) and caching (Redis)
- Familiarity with containerisation (Docker, Kubernetes)
- Solid understanding of distributed systems and microservices
- Excellent communication skills and ability to work in a remote team

Nice to Have
- Experience with real-time data streaming (Kafka, Spark)
- Contributions to open-source projects
- AWS or GCP certifications
"""


def create_sample_docx(path: Path) -> None:
    doc = Document()
    for text, bold in SAMPLE_RESUME_LINES:
        para = doc.add_paragraph()
        run = para.add_run(text)
        run.bold = bold
    doc.save(str(path))


def main() -> None:
    sample_dir = Path(__file__).parent / "samples"
    sample_dir.mkdir(exist_ok=True)
    resume_path = sample_dir / "sample_resume.docx"

    # ── Stage 1: Parsing & Segmentation ──────────────────────────────
    print("⏳ Running Stage 1 (Parsing & Segmentation)...")
    create_sample_docx(resume_path)
    resume_text = extract_resume_text(resume_path)
    statements = segment_resume(resume_text)
    jd_clean = clean_jd_text(SAMPLE_JD)

    # ── Stage 2: Explicit Skill Extraction ───────────────────────────
    print("⏳ Running Stage 2 (Explicit Skill Extraction)...")
    skill_dict = load_skill_dictionary()
    resume_skills = extract_resume_skills(statements, skill_dict)
    jd_skills = extract_jd_skills(jd_clean, skill_dict)
    stage2_output = {
        "resume_skills": resume_skills,
        "jd_required_skills": jd_skills,
    }

    # ── Stage 3: Inference Engine ────────────────────────────────────
    print("⏳ Running Stage 3 (Inference Engine)...")
    edges = load_skill_graph()
    graph = build_graph(edges)
    model = load_sbert_model()
    stage3_output = run_inference(stage2_output, graph, model)

    inferences = stage3_output["inferences"]

    # ── Stage 4: Question Generation & Verification ──────────────────
    print("\n" + "=" * 72)
    print("  STAGE 4: Clarifying Question Generation & Verification")
    print("=" * 72)

    # 1. Initialize verification status for all inferences
    inferences = initialize_verification_status(inferences)

    # 2. Generate questions for all NEEDS_VERIFICATION inferences
    templates = load_question_templates()
    questions = generate_all_questions(inferences, templates)

    print(f"\n❓ Generated Clarifying Questions ({len(questions)} items)")
    print("-" * 72)
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}] Missing Skill: {q['missing_skill']}")
        print(f"    Question: {q['question']}")
        print(f"    Options : {q['options']}")

    # 3. Simulate Candidate Responses
    # Let's answer the first question (Distributed Systems) with "Implemented it myself"
    # and also demonstrate a mock OAuth inference to match the prompt's example.
    target_skill = questions[0]["missing_skill"] if questions else "Distributed Systems"
    chosen_answer = "Implemented it myself"

    print(f"\n💬 Simulating Candidate Response:")
    print("-" * 72)
    print(f"Candidate answered for '{target_skill}': '{chosen_answer}'")

    updated_inferences = []
    for inf in inferences:
        if inf.get("missing_skill") == target_skill:
            updated_inf = apply_response(inf, chosen_answer)
            updated_inferences.append(updated_inf)
        else:
            updated_inferences.append(inf)

    print(f"\n🔍 Updated Inferences Status:")
    print("-" * 72)
    for inf in updated_inferences:
        v_flag = "✓ Verified" if inf.get("verified") else "✗ Unverified"
        print(f" • {inf['missing_skill']:<20} | Status: {inf['classification']:<20} | {v_flag}")

    # Also test an OAuth specific example if needed
    mock_oauth_inf = {
        "missing_skill": "OAuth",
        "matched_resume_skill": "Third-Party Login",
        "matched_statement": "Built the application with authentication and third-party login using Firebase.",
        "edge_weight": 0.85,
        "semantic_similarity": 0.81,
        "confidence": 78,
        "reasoning": "Your resume mentions 'third-party login', which commonly involves OAuth. Inferred with 78% confidence.",
        "classification": "NEEDS_VERIFICATION",
        "verified": False,
    }
    oauth_q = generate_all_questions([mock_oauth_inf], templates)[0]
    print(f"\n💡 Testing Example from Context (OAuth):")
    print("-" * 72)
    print(f"Question: {oauth_q['question']}")
    print(f"Options : {oauth_q['options']}")
    answered_oauth = apply_response(mock_oauth_inf, "Implemented it myself")
    print(f"Result  : Status={answered_oauth['classification']}, verified={answered_oauth['verified']}")

    # 4. JSON Output
    output = {
        "inferences": updated_inferences,
        "explicitly_matched": stage3_output["explicitly_matched"],
        "generated_questions": questions,
    }

    print("\n" + "=" * 72)
    print("  STAGE 4 JSON OUTPUT")
    print("=" * 72)
    print(json.dumps(output, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
