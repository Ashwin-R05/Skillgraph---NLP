"""
SkillGraph — Stage 6: Backend API Server

This module exposes the 5-stage SkillGraph NLP pipeline over HTTP:
  - POST /api/analyze: Receives resume file (PDF/DOCX) + job description text,
    runs Stages 1->2->3, initializes session, and returns initial match list
    and any clarifying questions (Stage 4). If no clarifying questions are needed,
    automatically compiles Stage 5 report.
  - POST /api/answer: Receives user response to a clarifying question, updates
    session inference state, and returns remaining question count.
  - GET /api/report/<session_id>: Runs Stage 5 compilation on session state and
    returns the complete candidate-facing report and rewrites.

Security Hardening:
  - Request size limit: MAX_CONTENT_LENGTH capped at 5 MB to prevent DoS.
  - Rate limiting: Flask-Limiter protects compute-heavy NLP endpoints.
  - Session TTL & eviction: Stale sessions pruned to prevent memory exhaustion.
  - Sanitized error responses: Prevents internal environment/stack disclosure.
"""

from __future__ import annotations

import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename

# Import pipeline stages without reimplementing logic
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
from skillgraph.reporter import (
    compile_report,
    generate_all_rewrites,
    build_final_output,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("skillgraph_api")

app = Flask(__name__)

# ── High-Level Security Fix 1: Max upload size (5 MB) ──
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

# Enable CORS for frontend integration
CORS(app)

# ── High-Level Security Fix 2: Rate Limiting to prevent compute exhaustion ──
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["120 per minute"],
    storage_uri="memory://",
)

# ── Session Store with Expiry / TTL (3600 seconds = 1 hour, max 500 items) ──
SESSIONS: dict[str, dict[str, Any]] = {}
SESSION_TTL_SECONDS: int = 3600
MAX_SESSIONS: int = 500


def cleanup_stale_sessions() -> None:
    """Evict expired sessions or prune if count exceeds MAX_SESSIONS."""
    now = time.time()
    expired = [
        sid for sid, data in SESSIONS.items()
        if now - data.get("created_at", now) > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        del SESSIONS[sid]

    # Enforce hard capacity bound
    while len(SESSIONS) > MAX_SESSIONS:
        oldest_sid = next(iter(SESSIONS))
        del SESSIONS[oldest_sid]


# Preload static assets/models at server startup
print("⏳ Initializing SkillGraph backend resources...")
SKILL_DICT = load_skill_dictionary()
GRAPH = build_graph(load_skill_graph())
QUESTION_TEMPLATES = load_question_templates()
SBERT_MODEL = load_sbert_model()
print("✓ SkillGraph backend ready.")

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def is_allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


# ── Error Handlers ──

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File size exceeds the 5 MB limit. Please upload a smaller file."}), 413


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded. Please wait a moment before trying again."}), 429


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "SkillGraph API"})


@app.route("/api/analyze", methods=["POST"])
@limiter.limit("10 per minute")  # Rate limit heavy ML/NLP extraction
def analyze():
    """Accepts multipart form-data: resume (file) + job_description (text).

    Runs Stages 1, 2, and 3, prepares Stage 4 questions, stores session state,
    and returns session_id, explicitly_matched skills, and questions.
    """
    cleanup_stale_sessions()

    if "resume" not in request.files:
        return jsonify({"error": "Missing 'resume' file in request"}), 400

    file = request.files["resume"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected"}), 400

    if not is_allowed_file(file.filename):
        return jsonify({
            "error": f"Unsupported file type. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400

    job_description = request.form.get("job_description", "").strip()
    if not job_description:
        return jsonify({"error": "Job description text cannot be empty"}), 400
    if len(job_description) > 50_000:
        return jsonify({"error": "Job description exceeds maximum allowed length of 50,000 characters."}), 400

    # Save uploaded file to a temporary location for Stage 1 parser
    filename = secure_filename(file.filename)
    suffix = Path(filename).suffix.lower()
    temp_dir = tempfile.mkdtemp(prefix="skillgraph_")
    temp_path = Path(temp_dir) / f"upload_{uuid.uuid4().hex[:8]}{suffix}"

    try:
        file.save(str(temp_path))

        # ── Stage 1: Parsing & Segmentation ──
        resume_text = extract_resume_text(temp_path)
        statements = segment_resume(resume_text)
        if not statements:
            return jsonify({"error": "Could not extract readable statements from resume"}), 400

        jd_clean = clean_jd_text(job_description)

        # ── Stage 2: Explicit Extraction ──
        resume_skills = extract_resume_skills(statements, SKILL_DICT)
        jd_skills = extract_jd_skills(jd_clean, SKILL_DICT)
        stage2_output = {
            "resume_skills": resume_skills,
            "jd_required_skills": jd_skills,
        }

        # ── Stage 3: Inference Engine ──
        stage3_output = run_inference(stage2_output, GRAPH, SBERT_MODEL)
        inferences = initialize_verification_status(stage3_output["inferences"])
        explicitly_matched = stage3_output["explicitly_matched"]

        # ── Stage 4: Question Generation ──
        questions = generate_all_questions(inferences, QUESTION_TEMPLATES)

        # Create session
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "created_at": time.time(),
            "statements": statements,
            "jd_clean": jd_clean,
            "explicitly_matched": explicitly_matched,
            "inferences": inferences,
            "questions": questions,
            "answered_skills": set(),
            "final_report": None,
        }

        # If there are no clarifying questions needed, compile Stage 5 report directly
        if not questions:
            stage4_output = {
                "inferences": inferences,
                "explicitly_matched": explicitly_matched,
            }
            report = compile_report(stage4_output)
            rewrites = generate_all_rewrites(report)
            session_data["final_report"] = build_final_output(report, rewrites)

        SESSIONS[session_id] = session_data

        response_payload = {
            "session_id": session_id,
            "explicitly_matched": explicitly_matched,
            "questions": questions,
            "immediate_report": session_data["final_report"] is not None,
        }
        if session_data["final_report"]:
            response_payload["report"] = session_data["final_report"]

        return jsonify(response_payload)

    except ValueError as ve:
        logger.warning("Validation error in resume analysis: %s", ve)
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.exception("Unexpected error during resume analysis")
        return jsonify({"error": "Failed to analyze resume. Please ensure the document is not password-protected or corrupted."}), 500
    finally:
        # Robust cleanup of temporary directory and uploaded file
        try:
            import shutil
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


@app.route("/api/answer", methods=["POST"])
@limiter.limit("60 per minute")
def answer_question():
    """Accepts JSON: { "session_id": "...", "missing_skill": "...", "selected_option": "..." }

    Updates the matched inference via Stage 4 apply_response and returns
    remaining question count.
    """
    cleanup_stale_sessions()

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    session_id = data.get("session_id")
    missing_skill = data.get("missing_skill")
    selected_option = data.get("selected_option")

    if not isinstance(session_id, str) or not isinstance(missing_skill, str) or not isinstance(selected_option, str):
        return jsonify({"error": "Missing or invalid types for required fields"}), 400

    if len(session_id) > 100 or len(missing_skill) > 100 or len(selected_option) > 200:
        return jsonify({"error": "Field length exceeds allowed limit"}), 400

    if not session_id or session_id not in SESSIONS:
        return jsonify({"error": "Invalid or expired session_id"}), 404

    if not missing_skill or not selected_option:
        return jsonify({"error": "Missing 'missing_skill' or 'selected_option'"}), 400

    session_data = SESSIONS[session_id]
    inferences = session_data["inferences"]

    updated = False
    for i, inf in enumerate(inferences):
        if inf.get("missing_skill") == missing_skill:
            inferences[i] = apply_response(inf, selected_option)
            session_data["answered_skills"].add(missing_skill)
            updated = True
            break

    if not updated:
        return jsonify({"error": f"Skill '{missing_skill}' not found in active session inferences"}), 400

    # Calculate remaining questions
    total_questions = len(session_data["questions"])
    answered_count = len(session_data["answered_skills"])
    remaining = max(0, total_questions - answered_count)

    return jsonify({
        "status": "success",
        "missing_skill": missing_skill,
        "remaining_questions": remaining,
    })


@app.route("/api/report/<session_id>", methods=["GET"])
@limiter.limit("60 per minute")
def get_report(session_id: str):
    """Compiles Stage 5 report and rewrites on the session's current state."""
    cleanup_stale_sessions()

    if not session_id or session_id not in SESSIONS:
        return jsonify({"error": "Invalid or expired session_id"}), 404

    session_data = SESSIONS[session_id]

    # If already compiled and no changes, return cached report
    if session_data.get("final_report") and len(session_data["answered_skills"]) == len(session_data["questions"]):
        return jsonify(session_data["final_report"])

    stage4_output = {
        "inferences": session_data["inferences"],
        "explicitly_matched": session_data["explicitly_matched"],
    }

    report = compile_report(stage4_output)
    rewrites = generate_all_rewrites(report)
    final_output = build_final_output(report, rewrites)

    session_data["final_report"] = final_output
    return jsonify(final_output)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting SkillGraph API server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
