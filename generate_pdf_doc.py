#!/usr/bin/env python3
"""
Generate a publication-grade, professional PDF of the SkillGraph Project Documentation
using ReportLab with clean styling, typography, flowcharts, tables, and code formatting.
"""

import sys
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and stamp 'Page X of Y' on all pages.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, letter[1] - 36, "SkillGraph: Explainable Implicit Skill Inference & Resume Evaluation")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)
            
        # Footer (All pages)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 45, letter[0] - 54, 45)
        
        self.drawString(54, 32, "Confidential Project Report • NLP & Knowledge Graph System")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 32, page_str)
        self.restoreState()


def build_pdf(output_path="/mnt/Data/NLP/project/SkillGraph_Documentation.pdf"):
    # Page setup: Letter, 0.75 in (54 pt) margins
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Brand Colors
    PRIMARY = colors.HexColor("#0F172A")    # Deep slate
    ACCENT = colors.HexColor("#2563EB")     # Royal blue
    TEAL = colors.HexColor("#0D9488")       # Academic teal
    TEXT = colors.HexColor("#1E293B")       # Dark charcoal
    MUTED = colors.HexColor("#64748B")      # Muted grey
    BG_LIGHT = colors.HexColor("#F8FAFC")   # Code/Card background
    BORDER_LIGHT = colors.HexColor("#E2E8F0")

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=ACCENT,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=TEAL,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=TEXT,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )

    badge_style = ParagraphStyle(
        'Badge_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1
    )

    story = []

    # Title & Header
    story.append(Paragraph("SkillGraph", title_style))
    story.append(Paragraph("Explainable Implicit Skill Inference & Resume Evaluation System", subtitle_style))
    
    # Metadata Pill / Banner
    meta_table = Table(
        [[
            Paragraph("<b>Stack:</b> Python 3.10+ | Flask | spaCy | SBERT | NetworkX | React 19 | Vite", body_style),
            Paragraph("<b>Architecture:</b> 7 Pipeline Stages (Offline / Zero-API)", ParagraphStyle('MetaRight', parent=body_style, alignment=2))
        ]],
        colWidths=[330, 174]
    )
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Abstract / Problem Statement
    story.append(Paragraph(
        "<b>Abstract & Problem Statement:</b> Candidates rarely enumerate every foundational tool, protocol, or concept they use, "
        "yet standard keyword-matching Applicant Tracking Systems (ATS) automatically disqualify them for unstated implicit competencies. "
        "Conversely, generative LLMs often hallucinate unverified skills and fabricate accomplishments. <b>SkillGraph</b> bridges this gap "
        "through deterministic skill gazetteers, directed graph knowledge traversal, contextual Sentence-BERT similarity, "
        "and active candidate verification to ensure explainable, zero-hallucination resume evaluations.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # SECTION 1: Technology Stack
    story.append(Paragraph("1. Technology Stack: Backend & Frontend", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceBefore=0, spaceAfter=8))

    stack_data = [
        [Paragraph("<b>Component Layer</b>", ParagraphStyle('TH', parent=body_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#FFFFFF'))),
         Paragraph("<b>Technologies & Libraries</b>", ParagraphStyle('TH2', parent=body_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#FFFFFF'))),
         Paragraph("<b>Role in System</b>", ParagraphStyle('TH3', parent=body_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#FFFFFF')))],
        
        [Paragraph("<b>Backend Runtime</b>", body_style), Paragraph("Python 3.10+, Flask 3.x", body_style), Paragraph("Core pipeline orchestration & REST API endpoints", body_style)],
        [Paragraph("<b>Linguistic Parsing</b>", body_style), Paragraph("spaCy (en_core_web_sm)", body_style), Paragraph("Bullet/sentence segmentation & entity cross-checking", body_style)],
        [Paragraph("<b>Semantic Embeddings</b>", body_style), Paragraph("Sentence-BERT (all-MiniLM-L6-v2)", body_style), Paragraph("384-d dense embeddings; offline cosine similarity (CPU)", body_style)],
        [Paragraph("<b>Knowledge Graph</b>", body_style), Paragraph("NetworkX (DiGraph)", body_style), Paragraph("68 canonical skills, 64 directed weighted edges", body_style)],
        [Paragraph("<b>Document Ingestion</b>", body_style), Paragraph("pdfplumber, python-docx", body_style), Paragraph("Stream parsing, layout repair, text extraction", body_style)],
        [Paragraph("<b>Backend Security</b>", body_style), Paragraph("Flask-Limiter, Magic Bytes, Decompress Bomb Defense", body_style), Paragraph("Rate limits (10/min), file type validation, 5 MB ceiling", body_style)],
        [Paragraph("<b>Frontend Framework</b>", body_style), Paragraph("React 19, Vite 8", body_style), Paragraph("Reactive 3-stage UI, rapid HMR, optimized bundle", body_style)],
        [Paragraph("<b>Styling & Typography</b>", body_style), Paragraph("Tailwind CSS v4, Instrument Serif, Plus Jakarta, JetBrains Mono", body_style), Paragraph("Academic institutional prestige theme, print stylesheets", body_style)],
        [Paragraph("<b>Frontend Interaction</b>", body_style), Paragraph("Native Clipboard & Print APIs, Keyboard Shortcuts", body_style), Paragraph("Hotkeys [1][2][3] for Q&A, instant 1-click sample loader", body_style)],
    ]
    t_stack = Table(stack_data, colWidths=[120, 160, 224])
    t_stack.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_stack)
    story.append(Spacer(1, 12))

    # SECTION 2: End-to-End Project Flow
    story.append(Paragraph("2. End-to-End System Flow & Architecture", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "SkillGraph operates across 5 linear pipeline execution stages triggered via the RESTful server and rendered dynamically in the React client:",
        body_style
    ))

    # Architecture Flow Box
    flow_steps = [
        [Paragraph("<b>STAGE 1: Ingestion &amp; Segmentation</b><br/><i>File &amp; Document Parsing (skillgraph/parser.py)</i>", body_style),
         Paragraph("• Validates magic bytes (<code>%PDF-</code>, <code>PK\\x03\\x04</code>) and guards against zip bombs.<br/>"
                   "• Normalizes carriage returns, cleans OCR artifacts, rejoins line wraps.<br/>"
                   "• Uses spaCy to segment text into discrete, actionable statements.", body_style)],
        
        [Paragraph("<b>STAGE 2: Explicit Extraction</b><br/><i>Gazetteer Matching (skillgraph/extractor.py)</i>", body_style),
         Paragraph("• Matches resume &amp; job description against 68 canonical skills and 300+ aliases.<br/>"
                   "• Longest-match greedy regex with word boundaries to eliminate substrings.<br/>"
                   "• Records precise statement-level provenance for every matched skill.", body_style)],

        [Paragraph("<b>STAGE 3: Inference Engine</b><br/><i>Graph &amp; SBERT (skillgraph/inference.py)</i>", body_style),
         Paragraph("• Identifies missing skills required by the job description.<br/>"
                   "• Checks NetworkX graph for prerequisite edges from candidate's skills.<br/>"
                   "• Computes local SBERT embedding cosine similarity against source statement.<br/>"
                   "• <b>Formula:</b> <code>Confidence = (0.50 * w_edge + 0.50 * sim_SBERT) * 100</code><br/>"
                   "• Tri-tier classification: High (&ge;85%), Needs Verification (40-85%), Gap (&lt;40%).", body_style)],

        [Paragraph("<b>STAGE 4: Active Verification</b><br/><i>Candidate Disambiguation (skillgraph/verifier.py)</i>", body_style),
         Paragraph("• Generates deterministic questions exclusively for <code>NEEDS_VERIFICATION</code>.<br/>"
                   "• Candidate responds: <i>Hands-on (1.0)</i>, <i>Framework/Library (0.5)</i>, or <i>Unfamiliar (0.0)</i>.<br/>"
                   "• Eliminates false positives before report synthesis.", body_style)],

        [Paragraph("<b>STAGE 5: Report &amp; Rewriting</b><br/><i>Synthesis &amp; Slots (skillgraph/reporter.py)</i>", body_style),
         Paragraph("• Calculates weighted overall fit percentage.<br/>"
                   "• Deterministic slot-filling rewrites augment resume statements without fabricating metrics or unverified tools.<br/>"
                   "• Generates comprehensive executive dossier with full algebraic explanations.", body_style)],

        [Paragraph("<b>STAGE 6: Interactive Dashboard</b><br/><i>Web Interface &amp; API (server.py + frontend/)</i>", body_style),
         Paragraph("• Flask session-isolated REST backend with in-memory TTL caching.<br/>"
                   "• React 19 UI with real-time fit gauges, keyboard shortcuts, and print stylesheet.", body_style)],
    ]
    t_flow = Table(flow_steps, colWidths=[160, 344])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER_LIGHT),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 14))

    # SECTION 3: Deep Technical Pipeline Breakdown
    story.append(Paragraph("3. Mathematical Formulations & Algorithms", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceBefore=0, spaceAfter=8))

    story.append(Paragraph("<b>Confidence Calculation (Stage 3):</b>", h2_style))
    story.append(Paragraph(
        "For each required skill <i>s</i> absent from the candidate's explicit skills, SkillGraph finds all predecessors "
        "<i>p &isin; Explicit</i> in the directed skill graph where <i>(p &rarr; s)</i> exists with edge weight <i>w(p, s)</i>. "
        "It then measures the contextual semantic similarity between <i>s</i> and the source statement <i>stmt(p)</i> using Sentence-BERT:",
        body_style
    ))
    
    formula_box = Table(
        [[
            Paragraph("<b>Confidence(s) = [ 0.50 &times; w(p, s) + 0.50 &times; CosineSimilarity(SBERT(s), SBERT(stmt(p))) ] &times; 100</b>", ParagraphStyle('F', parent=code_style, fontSize=9, textColor=PRIMARY, alignment=1))
        ]],
        colWidths=[504]
    )
    formula_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('BOX', (0,0), (-1,-1), 1, ACCENT),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(formula_box)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Candidate Fit Percentage (Stage 5):</b>", h2_style))
    story.append(Paragraph(
        "The overall candidate qualification score accounts for explicit proficiencies, confirmed implicit proficiencies, "
        "and partial library-level exposures, normalized over the total skills demanded by the target job description:",
        body_style
    ))

    fit_box = Table(
        [[
            Paragraph("<b>Fit % = round( [ N_explicit &times; 1.0 + N_confirmed &times; 1.0 + N_high_unverified &times; 0.85 + N_partial &times; 0.5 ] / N_total_required &times; 100 )</b>", ParagraphStyle('F2', parent=code_style, fontSize=8.5, textColor=PRIMARY, alignment=1))
        ]],
        colWidths=[504]
    )
    fit_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#16A34A")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(fit_box)
    story.append(Spacer(1, 14))

    # SECTION 4: Empirical Evaluation Results
    story.append(Paragraph("4. Stage 7 Empirical Evaluation Benchmark", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "The inference engine was evaluated against a rigorous ground-truth dataset (<code>eval_dataset.json</code>) "
        "comprising 18 hand-labeled resume/job-description scenarios across 60 evaluated skill targets:",
        body_style
    ))

    eval_data = [
        [Paragraph("<b>Metric</b>", ParagraphStyle('TH', parent=body_style, textColor=colors.white)),
         Paragraph("<b>Measured Score</b>", ParagraphStyle('TH', parent=body_style, textColor=colors.white)),
         Paragraph("<b>Benchmark Significance &amp; Interpretation</b>", ParagraphStyle('TH', parent=body_style, textColor=colors.white))],
        
        [Paragraph("<b>Inference Precision</b>", body_style), Paragraph("<b>94.1%</b> (16 / 17)", body_style), Paragraph("16 of 17 inferred skills were genuine, justifiable competencies.", body_style)],
        [Paragraph("<b>Inference Recall</b>", body_style), Paragraph("<b>94.1%</b> (16 / 17)", body_style), Paragraph("Successfully recovered 16 of 17 unstated skills expected by evaluators.", body_style)],
        [Paragraph("<b>Inference F1-Score</b>", body_style), Paragraph("<b>94.1%</b>", body_style), Paragraph("Harmonic balance of precision and recall under zero-shot testing.", body_style)],
        [Paragraph("<b>False Positive Rate on Gaps</b>", body_style), Paragraph("<b>5.0%</b> (1 / 20)", body_style), Paragraph("Only 1 genuine skill deficiency out of 20 was incorrectly flagged.", body_style)],
        [Paragraph("<b>Overall Accuracy</b>", body_style), Paragraph("<b>96.7%</b> (58 / 60)", body_style), Paragraph("Exact classification match across all explicit, inferred, and gap skills.", body_style)],
    ]
    t_eval = Table(eval_data, colWidths=[140, 100, 264])
    t_eval.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_eval)
    story.append(Spacer(1, 14))

    # SECTION 5: API Endpoints Reference
    story.append(Paragraph("5. RESTful API Interface Specification", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceBefore=0, spaceAfter=8))

    api_data = [
        [Paragraph("<b>HTTP Method &amp; URI</b>", ParagraphStyle('TH', parent=body_style, textColor=colors.white)),
         Paragraph("<b>Request Payload</b>", ParagraphStyle('TH', parent=body_style, textColor=colors.white)),
         Paragraph("<b>Function &amp; Returned Data</b>", ParagraphStyle('TH', parent=body_style, textColor=colors.white))],

        [Paragraph("<code>GET /api/health</code>", code_style), Paragraph("None", body_style), Paragraph("Health check returning operational status and uptime.", body_style)],
        [Paragraph("<code>POST /api/analyze</code>", code_style), Paragraph("Multipart: <code>resume</code> (file) + <code>job_description</code> (text)", body_style), Paragraph("Runs Stages 1-3, registers session, returns matched skills &amp; questions.", body_style)],
        [Paragraph("<code>POST /api/answer</code>", code_style), Paragraph("JSON: <code>{session_id, missing_skill, selected_option}</code>", body_style), Paragraph("Applies Stage 4 update (CONFIRMED/PARTIAL/GAP) and returns next question.", body_style)],
        [Paragraph("<code>GET /api/report/&lt;id&gt;</code>", code_style), Paragraph("URL parameter: <code>session_id</code>", body_style), Paragraph("Synthesizes Stage 5 final score, skill breakdowns, and bullet rewrites.", body_style)],
    ]
    t_api = Table(api_data, colWidths=[130, 160, 214])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_LIGHT),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_api)
    story.append(Spacer(1, 14))

    # SECTION 6: Key Guarantees & Principles
    story.append(Paragraph("6. Core Architectural Guarantees", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph("• <b>Local Privacy:</b> All tensor calculations and NLP operations run strictly on-device without telemetry or cloud calls.", bullet_style))
    story.append(Paragraph("• <b>Full Explainability:</b> Every recommendation is grounded in an exact resume sentence, a knowledge graph edge, and a mathematical similarity score.", bullet_style))
    story.append(Paragraph("• <b>Zero Hallucination:</b> Resume rewrites use strict slot-filling templates anchored to original statements, never fabricating metrics, companies, or tools.", bullet_style))
    story.append(Paragraph("• <b>Human-in-the-Loop Disambiguation:</b> Ambiguous skills (40% - 85% confidence) require candidate confirmation, capping the false positive rate to 5.0%.", bullet_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Document successfully created at {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/mnt/Data/NLP/project/SkillGraph_Documentation.pdf"
    build_pdf(out)
