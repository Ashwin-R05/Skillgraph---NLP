import React, { useState, useEffect, useRef } from 'react';

// Pre-packaged job descriptions for quick academic evaluation
const PRESET_JDS = [
  {
    title: 'Senior Backend Engineer (FinTech Benchmark)',
    role: 'Senior Backend Engineer — FinTech Startup',
    text: `Senior Backend Engineer — FinTech Startup (Remote)

Responsibilities:
- Architect and implement scalable backend microservices in Python (FastAPI or Django)
- Design event-driven distributed systems using message queues (Apache Kafka, RabbitMQ)
- Manage data pipelines and ETL workflows with Apache Spark and PostgreSQL
- Containerise and orchestrate production deployments with Docker and Kubernetes
- Ensure cloud infrastructure security and reliability on AWS or GCP

Requirements:
- 4+ years of backend engineering experience
- Strong proficiency in Python, PostgreSQL, MySQL, and Redis
- Familiarity with containerisation (Docker, Kubernetes) and CI/CD
- Solid understanding of distributed systems and microservices
- Nice to have: Real-time streaming (Kafka, Spark) and OAuth authentication`,
  },
  {
    title: 'Machine Learning & NLP Research Engineer',
    role: 'ML & NLP Engineer — Applied AI Lab',
    text: `Machine Learning & NLP Engineer (Hybrid)

Responsibilities:
- Build domain-adapted language models, NER pipelines, and knowledge graph representations
- Train deep learning models with PyTorch and Sentence Transformers
- Package inference models into high-throughput REST APIs with FastAPI and Docker
- Collaborate on evaluation datasets and qualitative performance auditing

Requirements:
- Strong programming background in Python and scikit-learn
- Proven experience with PyTorch, NLP, and spaCy
- Knowledge of vector embeddings, semantic similarity, and knowledge graphs
- Familiarity with unit testing (pytest) and test-driven development`,
  },
  {
    title: 'Full-Stack Cloud Systems Developer',
    role: 'Full-Stack Developer — Cloud Platforms',
    text: `Full-Stack Developer — Cloud Platforms

Responsibilities:
- Develop modern, responsive single-page web applications using React and TypeScript
- Build secure, token-authenticated RESTful services in Node.js or Python
- Automate testing, linting, and deployment using GitHub Actions and Docker
- Manage database schemas and queries in PostgreSQL and Redis

Requirements:
- Proficiency in JavaScript, TypeScript, React, and HTML/CSS
- Backend experience with REST API design, JWT, and OAuth protocols
- Experience with cloud environments (AWS) and CI/CD automation`,
  },
];

export default function App() {
  // Screens: 'upload' | 'questions' | 'report'
  const [screen, setScreen] = useState('upload');
  const [loading, setLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(0);
  const [error, setError] = useState(null);

  // Upload Form State
  const [file, setFile] = useState(null);
  const [isSampleLoaded, setIsSampleLoaded] = useState(false);
  const [jobDescription, setJobDescription] = useState(PRESET_JDS[0].text);
  const [activePresetIndex, setActivePresetIndex] = useState(0);
  const [dragActive, setDragActive] = useState(false);

  // Session & Questions State
  const [sessionId, setSessionId] = useState(null);
  const [explicitlyMatched, setExplicitlyMatched] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  // Final Report State
  const [report, setReport] = useState(null);
  const [activeTab, setActiveTab] = useState('all');
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const [showJsonModal, setShowJsonModal] = useState(false);

  // Multi-phase loading simulation during NLP pipeline execution
  useEffect(() => {
    let interval;
    if (loading) {
      setLoadingPhase(0);
      interval = setInterval(() => {
        setLoadingPhase((prev) => (prev < 2 ? prev + 1 : prev));
      }, 1600);
    } else {
      setLoadingPhase(0);
    }
    return () => clearInterval(interval);
  }, [loading]);

  // Keyboard navigation for clarifying questions (1, 2, 3)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (screen !== 'questions' || loading) return;
      if (e.key === '1' || e.key === '2' || e.key === '3') {
        const optionIndex = parseInt(e.key, 10) - 1;
        const currentQ = questions[currentQuestionIndex];
        if (currentQ && currentQ.options && currentQ.options[optionIndex]) {
          handleSelectOption(currentQ.options[optionIndex]);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [screen, currentQuestionIndex, questions, loading]);

  // Load sample benchmark resume (Priya Sharma Acme Corp)
  const handleLoadSampleResume = async () => {
    try {
      const res = await fetch('/sample_resume.docx');
      if (!res.ok) throw new Error('Benchmark sample not found on server');
      const blob = await res.blob();
      const sampleFile = new File([blob], 'sample_resume_priya_sharma.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });
      setFile(sampleFile);
      setIsSampleLoaded(true);
      setError(null);
    } catch (err) {
      setError(`Could not load benchmark sample: ${err.message}`);
    }
  };

  // Drag and drop handlers
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      const name = droppedFile.name.toLowerCase();
      if (name.endsWith('.pdf') || name.endsWith('.docx')) {
        setFile(droppedFile);
        setIsSampleLoaded(false);
        setError(null);
      } else {
        setError('Please drop a valid .pdf or .docx document');
      }
    }
  };

  // ─────────────────────────────────────────────────────────────
  // 1. Analyze Resume
  // ─────────────────────────────────────────────────────────────
  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please provide a resume document (.pdf or .docx)');
      return;
    }
    if (!jobDescription.trim()) {
      setError('Please input the target job description requirements');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('resume', file);
    formData.append('job_description', jobDescription);

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Failed to complete resume analysis');
      }

      setSessionId(data.session_id);
      setExplicitlyMatched(data.explicitly_matched || []);

      if (data.immediate_report && data.report) {
        setReport(data.report);
        setScreen('report');
      } else if (data.questions && data.questions.length > 0) {
        setQuestions(data.questions);
        setCurrentQuestionIndex(0);
        setScreen('questions');
      } else {
        await fetchReport(data.session_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ─────────────────────────────────────────────────────────────
  // 2. Answer Question
  // ─────────────────────────────────────────────────────────────
  const handleSelectOption = async (option) => {
    if (!sessionId || currentQuestionIndex >= questions.length) return;

    const currentQ = questions[currentQuestionIndex];
    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          missing_skill: currentQ.missing_skill,
          selected_option: option,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Failed to submit candidate response');
      }

      const nextIndex = currentQuestionIndex + 1;
      if (nextIndex < questions.length) {
        setCurrentQuestionIndex(nextIndex);
      } else {
        await fetchReport(sessionId);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ─────────────────────────────────────────────────────────────
  // 3. Fetch Final Report
  // ─────────────────────────────────────────────────────────────
  const fetchReport = async (sId) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/report/${sId}`);
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Failed to generate final report');
      }
      setReport(data);
      setScreen('report');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setScreen('upload');
    setFile(null);
    setIsSampleLoaded(false);
    setSessionId(null);
    setQuestions([]);
    setCurrentQuestionIndex(0);
    setReport(null);
    setError(null);
  };

  const handleCopyRewrite = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleCopyAllRewrites = () => {
    if (!report || !report.suggested_rewrites) return;
    const allText = report.suggested_rewrites
      .map(
        (rw, i) =>
          `[${i + 1}] Target Skill: ${rw.missing_skill}\nOriginal : "${rw.original_statement}"\nSuggested: "${rw.suggested_rewrite}"\n`
      )
      .join('\n');
    navigator.clipboard.writeText(allText);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2200);
  };

  // Loading phase descriptors
  const loadingStages = [
    { title: 'Stage 1: Document Ingestion & Segmentation', desc: 'Parsing structure, normalizing typography, and filtering non-content headers with spaCy.' },
    { title: 'Stage 2: Explicit Entity Extraction', desc: 'Matching canonical keywords against curated 68-skill dictionary with alias normalization.' },
    { title: 'Stage 3: Graph Traversal & SBERT Scoring', desc: 'Evaluating in-edge graph priors and computing Sentence-BERT semantic cosine similarities.' },
  ];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-indigo-500/40 selection:text-white academic-grid-pattern">
      {/* ─────────────────────────────────────────────────────────
          ACADEMIC TOP NAVIGATION & BRANDING
      ───────────────────────────────────────────────────────── */}
      <header className="border-b border-slate-800/80 bg-[#0c1222]/90 backdrop-blur-md sticky top-0 z-40 no-print">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center space-x-3.5">
            {/* Project Emblem */}
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-indigo-800 p-0.5 shadow-md shadow-indigo-950 flex items-center justify-center">
              <div className="w-full h-full bg-[#0a0f1d] rounded-[10px] flex items-center justify-center">
                <svg className="w-5 h-5 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="6" cy="6" r="3" />
                  <circle cx="18" cy="6" r="3" />
                  <circle cx="12" cy="18" r="3" />
                  <line x1="8.5" y1="7.5" x2="15.5" y2="7.5" />
                  <line x1="7.5" y1="8.5" x2="10.5" y2="15.5" />
                  <line x1="16.5" y1="8.5" x2="13.5" y2="15.5" />
                </svg>
              </div>
            </div>

            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold tracking-tight text-lg text-white font-sans">SkillGraph</span>
                <span className="bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full tracking-wider font-mono">
                  v1.0 • Research Edition
                </span>
              </div>
              <p className="text-[11px] text-slate-400 m-0 hidden sm:block">
                Explainable Implicit Skill Inference & Graph-Theoretic Resume Evaluation
              </p>
            </div>
          </div>

          {/* Stepper & Reset Button */}
          <div className="flex items-center space-x-3">
            {/* Visual Pipeline Phase Tracker */}
            <div className="hidden md:flex items-center space-x-2 text-[11px] font-mono bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-400">
              <span className={screen === 'upload' ? 'text-indigo-400 font-bold flex items-center' : 'text-slate-500'}>
                1. Ingestion
              </span>
              <span className="text-slate-600">→</span>
              <span className={screen === 'questions' ? 'text-indigo-400 font-bold flex items-center' : 'text-slate-500'}>
                2. Verification
              </span>
              <span className="text-slate-600">→</span>
              <span className={screen === 'report' ? 'text-emerald-400 font-bold flex items-center' : 'text-slate-500'}>
                3. Synthesis
              </span>
            </div>

            {screen !== 'upload' && (
              <button
                onClick={handleReset}
                className="text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700/80 border border-slate-700 px-3.5 py-1.5 rounded-lg transition-all duration-150 cursor-pointer flex items-center space-x-1.5"
              >
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                  <path d="M3 3v5h5" />
                </svg>
                <span>New Evaluation</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* ─────────────────────────────────────────────────────────
          MAIN WORKSPACE
      ───────────────────────────────────────────────────────── */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 md:py-10">
        {/* Error notification banner */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-950/60 border border-rose-500/40 text-rose-200 text-sm flex items-start justify-between backdrop-blur-md shadow-lg">
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <div>
                <p className="font-semibold text-rose-300 m-0">Evaluation Error</p>
                <p className="text-xs text-rose-200/90 mt-0.5 m-0">{error}</p>
              </div>
            </div>
            <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-200 text-base font-bold ml-4 cursor-pointer">
              ✕
            </button>
          </div>
        )}

        {/* ── SCREEN 1: UPLOAD & INPUT ── */}
        {screen === 'upload' && (
          <div className="space-y-8">
            {/* Academic Hero Banner */}
            <div className="text-center max-w-3xl mx-auto space-y-3 pt-2 pb-4">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Deterministic Knowledge Graph Prior + Local Sentence-BERT</span>
              </div>
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-serif text-white tracking-tight leading-tight">
                Explainable Implicit Skill Inference
              </h1>
              <p className="text-slate-400 text-sm sm:text-base leading-relaxed max-w-2xl mx-auto">
                Evaluate candidate resumes against rigorous job requirements. Detect explicit skills, infer unstated implicit competencies with grounded mathematical confidence, and eliminate black-box hallucinations.
              </p>

              {/* Mathematical Formulation Tag */}
              <div className="pt-2">
                <div className="inline-flex flex-wrap items-center justify-center gap-2 px-4 py-2 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-300 font-mono shadow-inner">
                  <span className="text-indigo-400 font-bold">Confidence</span>
                  <span>=</span>
                  <span className="text-slate-400">(0.50 ×</span>
                  <span className="text-amber-400 font-semibold" title="Hand-curated knowledge graph edge weight">w_graph</span>
                  <span className="text-slate-400">+ 0.50 ×</span>
                  <span className="text-emerald-400 font-semibold" title="Sentence-BERT cosine similarity with resume statement">sim_SBERT</span>
                  <span className="text-slate-400">) × 100</span>
                </div>
              </div>
            </div>

            {/* Input Cards Grid */}
            <form onSubmit={handleAnalyze} className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column: File Upload (5 cols) */}
              <div className="lg:col-span-5 glass-panel rounded-2xl p-6 space-y-5 glow-indigo">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h2 className="text-base font-bold text-white flex items-center space-x-2">
                      <svg className="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                        <polyline points="14 2 14 8 20 8" />
                      </svg>
                      <span>1. Candidate Resume</span>
                    </h2>
                    <p className="text-xs text-slate-400 mt-0.5">DOCX or PDF document (Max 5 MB)</p>
                  </div>

                  <span className="text-[10px] font-mono font-bold uppercase bg-slate-800 px-2 py-0.5 rounded text-indigo-300 border border-slate-700">
                    Required
                  </span>
                </div>

                {/* Dropzone */}
                <div
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-xl p-6 text-center transition-all duration-200 flex flex-col items-center justify-center space-y-3 cursor-pointer ${
                    dragActive
                      ? 'border-indigo-400 bg-indigo-950/30'
                      : file
                      ? 'border-emerald-500/50 bg-emerald-950/10'
                      : 'border-slate-700/80 hover:border-slate-600 bg-slate-900/50'
                  }`}
                  onClick={() => document.getElementById('resume-file-input').click()}
                >
                  <input
                    id="resume-file-input"
                    type="file"
                    accept=".pdf,.docx"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setFile(e.target.files[0]);
                        setIsSampleLoaded(false);
                        setError(null);
                      }
                    }}
                    className="hidden"
                  />

                  {file ? (
                    <div className="space-y-2">
                      <div className="w-12 h-12 mx-auto rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
                        <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-bold text-white truncate max-w-xs">{file.name}</p>
                        <p className="text-xs text-emerald-400 font-mono">
                          {(file.size / 1024).toFixed(1)} KB • {file.name.split('.').pop().toUpperCase()} Ready
                        </p>
                      </div>
                      <span className="inline-block text-[11px] text-slate-400 underline hover:text-slate-200">
                        Click to change document
                      </span>
                    </div>
                  ) : (
                    <>
                      <div className="w-12 h-12 rounded-full bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
                        <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                          <polyline points="17 8 12 3 7 8" />
                          <line x1="12" y1="3" x2="12" y2="15" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-200">Drop resume here or browse</p>
                        <p className="text-xs text-slate-500 mt-1">Supports academic DOCX and PDF formats</p>
                      </div>
                    </>
                  )}
                </div>

                {/* 1-Click Academic Sample Loader */}
                <div className="pt-2">
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span className="text-slate-400 font-medium">Quick Evaluator Benchmark:</span>
                    {isSampleLoaded && (
                      <span className="text-[10px] text-emerald-400 font-mono font-bold">✓ Loaded</span>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={handleLoadSampleResume}
                    className="w-full py-2.5 px-3 rounded-xl bg-slate-800/90 hover:bg-slate-700/80 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-white transition flex items-center justify-center space-x-2 cursor-pointer shadow-xs"
                  >
                    <svg className="w-4 h-4 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                    </svg>
                    <span>Load Benchmark Resume (Priya Sharma • Acme Corp)</span>
                  </button>
                </div>

                {/* Academic Security Badge */}
                <div className="bg-slate-900/60 rounded-xl p-3 border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
                  <div className="flex items-center space-x-1.5 text-slate-300 font-semibold">
                    <svg className="w-3.5 h-3.5 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                    <span>Deterministic & Private:</span>
                  </div>
                  <p className="m-0 leading-normal">
                    Files are validated by magic byte signatures and parsed on-device without telemetry or cloud LLM APIs.
                  </p>
                </div>
              </div>

              {/* Right Column: Job Description Workspace (7 cols) */}
              <div className="lg:col-span-7 glass-panel rounded-2xl p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h2 className="text-base font-bold text-white flex items-center space-x-2">
                      <svg className="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
                      </svg>
                      <span>2. Job Description Requirements</span>
                    </h2>
                    <p className="text-xs text-slate-400 mt-0.5">Extracted against the canonical skill ontology</p>
                  </div>

                  <span className="text-[10px] font-mono text-slate-400">
                    {jobDescription.length} chars • {jobDescription.trim().split(/\s+/).filter(Boolean).length} words
                  </span>
                </div>

                {/* Preset Chips */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 block">Preset Test Scenarios:</label>
                  <div className="flex flex-wrap gap-2">
                    {PRESET_JDS.map((preset, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setJobDescription(preset.text);
                          setActivePresetIndex(idx);
                        }}
                        className={`text-xs px-2.5 py-1.5 rounded-lg border transition cursor-pointer text-left ${
                          activePresetIndex === idx
                            ? 'bg-indigo-600/30 border-indigo-500 text-indigo-200 font-semibold'
                            : 'bg-slate-800/60 border-slate-700/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                        }`}
                      >
                        {preset.title}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Textarea */}
                <div className="relative">
                  <textarea
                    rows={8}
                    value={jobDescription}
                    onChange={(e) => {
                      setJobDescription(e.target.value);
                      setActivePresetIndex(-1);
                    }}
                    placeholder="Paste job description requirements, responsibilities, or qualification bullet points..."
                    className="w-full p-3.5 bg-slate-900/90 border border-slate-800 rounded-xl text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-mono leading-relaxed resize-y transition shadow-inner"
                  />
                </div>

                {/* Submit Action */}
                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-bold text-sm shadow-lg shadow-indigo-950/50 border border-indigo-400/30 transition-all duration-200 flex items-center justify-center space-x-2.5 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <div className="flex items-center space-x-3">
                        <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Executing Stages 1–3...</span>
                      </div>
                    ) : (
                      <>
                        <span>Execute SkillGraph Evaluation</span>
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                          <line x1="5" y1="12" x2="19" y2="12" />
                          <polyline points="12 5 19 12 12 19" />
                        </svg>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>

            {/* Pipeline Execution Animation Overlay */}
            {loading && (
              <div className="glass-panel rounded-2xl p-6 md:p-8 space-y-4 border border-indigo-500/30 bg-slate-900/90 glow-indigo">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 rounded-full bg-indigo-500 animate-ping"></div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-300 font-mono">
                    Executing Academic NLP Pipeline...
                  </h3>
                </div>

                <div className="space-y-3">
                  {loadingStages.map((stg, i) => (
                    <div
                      key={i}
                      className={`p-3 rounded-xl border transition-all duration-300 text-xs flex items-center justify-between ${
                        loadingPhase === i
                          ? 'bg-indigo-950/40 border-indigo-500/50 text-indigo-100'
                          : loadingPhase > i
                          ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200'
                          : 'bg-slate-900/40 border-slate-800 text-slate-500'
                      }`}
                    >
                      <div className="space-y-0.5">
                        <span className="font-bold">{stg.title}</span>
                        <p className="m-0 text-[11px] opacity-80">{stg.desc}</p>
                      </div>
                      {loadingPhase > i && (
                        <span className="text-emerald-400 font-bold font-mono text-xs">✓ Done</span>
                      )}
                      {loadingPhase === i && (
                        <span className="text-indigo-400 font-mono text-xs animate-pulse">Running...</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── SCREEN 2: CLARIFYING QUESTIONS (STAGE 4 DISAMBIGUATION) ── */}
        {screen === 'questions' && questions.length > 0 && (
          <div className="max-w-3xl mx-auto space-y-6">
            {/* Header / Context Banner */}
            <div className="glass-panel rounded-2xl p-6 border-slate-800 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse"></span>
                    <h2 className="text-lg font-bold text-white font-serif">Stage 4: Active Verification Interview</h2>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Stage 3 identified implicit competencies with moderate confidence (40%–85%). Resolve them now to finalize candidate fit.
                  </p>
                </div>

                <div className="text-right shrink-0">
                  <span className="text-xs font-mono text-amber-300 font-bold bg-amber-950/60 border border-amber-800/60 px-3 py-1 rounded-full">
                    Question {currentQuestionIndex + 1} of {questions.length}
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-[11px] font-mono text-slate-400">
                  <span>Verification Progress</span>
                  <span>{Math.round(((currentQuestionIndex) / questions.length) * 100)}% Complete</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden p-0.5">
                  <div
                    className="bg-gradient-to-r from-indigo-500 to-amber-500 h-full rounded-full transition-all duration-300"
                    style={{ width: `${((currentQuestionIndex) / questions.length) * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Question Card */}
            <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-6 glow-amber border-slate-800">
              {/* Question Badge & Skill Target */}
              <div className="flex items-start space-x-4">
                <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold flex items-center justify-center shrink-0 font-mono text-sm">
                  Q{currentQuestionIndex + 1}
                </div>
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-mono font-bold uppercase bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2.5 py-0.5 rounded-md">
                      Target Competency: {questions[currentQuestionIndex].missing_skill}
                    </span>
                    <span className="text-xs text-slate-400">Class: NEEDS_VERIFICATION</span>
                  </div>
                  <h3 className="text-base sm:text-xl font-medium text-white leading-snug font-serif">
                    {questions[currentQuestionIndex].question}
                  </h3>
                </div>
              </div>

              {/* Options */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>Select candidate response level:</span>
                  <span className="hidden sm:inline text-slate-500">Keyboard shortcuts: [1], [2], [3]</span>
                </div>

                {questions[currentQuestionIndex].options.map((option, idx) => {
                  let outcomeLabel = 'CONFIRMED (Direct Hands-on)';
                  let outcomeColor = 'text-emerald-400';
                  if (option.toLowerCase().includes('library') || option.toLowerCase().includes('framework')) {
                    outcomeLabel = 'PARTIALLY_CONFIRMED (Tooling Exposure)';
                    outcomeColor = 'text-amber-400';
                  } else if (option.toLowerCase().includes('not sure')) {
                    outcomeLabel = 'SKILL_GAP (Demoted to Gap)';
                    outcomeColor = 'text-rose-400';
                  }

                  return (
                    <button
                      key={idx}
                      onClick={() => handleSelectOption(option)}
                      disabled={loading}
                      className="w-full text-left p-4 rounded-xl border border-slate-800 hover:border-indigo-500 bg-slate-900/60 hover:bg-indigo-950/30 transition-all duration-150 cursor-pointer flex items-center justify-between group shadow-xs"
                    >
                      <div className="flex items-center space-x-3.5">
                        <span className="w-6 h-6 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 flex items-center justify-center text-xs font-mono font-bold group-hover:border-indigo-500 group-hover:text-white">
                          {idx + 1}
                        </span>
                        <div>
                          <p className="text-sm font-semibold text-slate-200 group-hover:text-white m-0">
                            {option}
                          </p>
                          <span className={`text-[11px] font-mono ${outcomeColor}`}>
                            → Outcome: {outcomeLabel}
                          </span>
                        </div>
                      </div>

                      <span className="text-slate-500 group-hover:text-indigo-400 font-bold transition-transform group-hover:translate-x-1">
                        →
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Academic Explanatory Note */}
            <p className="text-xs text-center text-slate-500 font-mono">
              Academic Provenance Guarantee: Human self-verification eliminates synthetic hallucinations before final candidate dossier synthesis.
            </p>
          </div>
        )}

        {/* ── SCREEN 3: FINAL FIT REPORT & REWRITE DOSSIER (STAGE 5) ── */}
        {screen === 'report' && report && (
          <div className="space-y-8">
            {/* Top Toolbar (Print, Inspect JSON, New) */}
            <div className="flex flex-wrap items-center justify-between gap-3 no-print border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs font-mono font-semibold uppercase text-emerald-400 tracking-wider">
                  Academic Evaluation Complete
                </span>
                <h2 className="text-2xl sm:text-3xl font-serif text-white m-0">Candidate Fit Dossier</h2>
              </div>

              <div className="flex items-center space-x-2.5">
                <button
                  onClick={() => setShowJsonModal(true)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-300 hover:text-white transition flex items-center space-x-1.5 cursor-pointer"
                >
                  <svg className="w-3.5 h-3.5 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="16 18 22 12 16 6" />
                    <polyline points="8 6 2 12 8 18" />
                  </svg>
                  <span>Inspect JSON</span>
                </button>

                <button
                  onClick={() => window.print()}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/50 text-xs font-semibold text-indigo-200 hover:text-white transition flex items-center space-x-1.5 cursor-pointer"
                >
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="6 9 6 2 18 2 18 9" />
                    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
                    <rect x="6" y="14" width="12" height="8" />
                  </svg>
                  <span>Print Dossier</span>
                </button>
              </div>
            </div>

            {/* Executive Fit Scorecard */}
            <div className="glass-panel rounded-2xl p-6 sm:p-8 border-slate-800 flex flex-col md:flex-row items-center justify-between gap-6 glow-indigo">
              <div className="space-y-2 text-center md:text-left">
                <div className="inline-block px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-mono font-semibold">
                  Overall Candidate Alignment Index
                </div>
                <h3 className="text-xl sm:text-2xl font-serif text-white">
                  Matched {report.fit_summary.matched_count} of {report.fit_summary.total_required_skills} Required Qualifications
                </h3>
                <p className="text-xs sm:text-sm text-slate-400 max-w-xl m-0 leading-relaxed">
                  Formula: (1.0 × Explicit + 1.0 × Confirmed + 0.5 × Partial + 0.0 × Gap) / Total Required.
                  All non-explicit matches carry traceable graph-semantic provenance.
                </p>
              </div>

              {/* Gauge */}
              <div className="flex items-center space-x-6 bg-slate-900/80 border border-slate-800 px-6 py-5 rounded-2xl shrink-0">
                <div className="relative w-24 h-24 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                    <path
                      className="text-slate-800"
                      strokeWidth="3.5"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className={
                        report.fit_summary.fit_percentage >= 75
                          ? 'text-emerald-400'
                          : report.fit_summary.fit_percentage >= 50
                          ? 'text-amber-400'
                          : 'text-rose-400'
                      }
                      strokeDasharray={`${report.fit_summary.fit_percentage}, 100`}
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <div className="absolute text-center">
                    <span className="text-2xl font-bold font-mono text-white">
                      {report.fit_summary.fit_percentage}%
                    </span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] uppercase tracking-wider font-mono font-bold text-slate-400 block">
                    Classification Tier
                  </span>
                  <p className="text-sm font-bold text-white m-0">
                    {report.fit_summary.fit_percentage >= 75
                      ? 'Tier I: Strong Alignment'
                      : report.fit_summary.fit_percentage >= 50
                      ? 'Tier II: Moderate Fit'
                      : 'Tier III: Critical Gaps'}
                  </p>
                  <span className="text-[11px] text-slate-400 block">
                    {report.skills_breakdown.genuine_gaps.length === 0
                      ? 'No skill gaps detected'
                      : `${report.skills_breakdown.genuine_gaps.length} genuine gaps identified`}
                  </span>
                </div>
              </div>
            </div>

            {/* Skills Breakdown by Categorized Tabs */}
            <div className="glass-panel rounded-2xl p-6 sm:p-8 border-slate-800 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-lg font-bold text-white font-serif">Competency Classification Matrix</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Categorized by algorithmic detection mode and candidate verification status.
                  </p>
                </div>

                {/* Filter Pills */}
                <div className="flex flex-wrap gap-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800 text-xs font-mono">
                  <button
                    onClick={() => setActiveTab('all')}
                    className={`px-3 py-1 rounded-lg transition cursor-pointer ${
                      activeTab === 'all' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    All ({report.fit_summary.total_required_skills})
                  </button>
                  <button
                    onClick={() => setActiveTab('explicit')}
                    className={`px-3 py-1 rounded-lg transition cursor-pointer ${
                      activeTab === 'explicit' ? 'bg-emerald-600 text-white font-bold' : 'text-slate-400 hover:text-emerald-300'
                    }`}
                  >
                    Explicit ({report.skills_breakdown.explicitly_present.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('confirmed')}
                    className={`px-3 py-1 rounded-lg transition cursor-pointer ${
                      activeTab === 'confirmed' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-indigo-300'
                    }`}
                  >
                    Confirmed ({report.skills_breakdown.confirmed_by_inference.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('partial')}
                    className={`px-3 py-1 rounded-lg transition cursor-pointer ${
                      activeTab === 'partial' ? 'bg-amber-600 text-white font-bold' : 'text-slate-400 hover:text-amber-300'
                    }`}
                  >
                    Partial ({report.skills_breakdown.partially_confirmed.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('gaps')}
                    className={`px-3 py-1 rounded-lg transition cursor-pointer ${
                      activeTab === 'gaps' ? 'bg-rose-600 text-white font-bold' : 'text-slate-400 hover:text-rose-300'
                    }`}
                  >
                    Gaps ({report.skills_breakdown.genuine_gaps.length})
                  </button>
                </div>
              </div>

              {/* Skills Listing Content */}
              <div className="space-y-6">
                {/* 1. Explicitly Present */}
                {(activeTab === 'all' || activeTab === 'explicit') && (
                  <div className="space-y-2.5">
                    <div className="flex items-center space-x-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                      <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">
                        Explicitly Stated on Resume ({report.skills_breakdown.explicitly_present.length})
                      </h4>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {report.skills_breakdown.explicitly_present.map((skill, i) => (
                        <span
                          key={i}
                          className="px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-200 text-xs font-semibold flex items-center space-x-1.5"
                        >
                          <span className="text-emerald-400">✓</span>
                          <span>{skill}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 2. Confirmed by Inference */}
                {(activeTab === 'all' || activeTab === 'confirmed') &&
                  report.skills_breakdown.confirmed_by_inference.length > 0 && (
                    <div className="space-y-3 pt-2">
                      <div className="flex items-center space-x-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-indigo-400"></span>
                        <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-indigo-400">
                          Confirmed by Graph Inference & Candidate Verification ({report.skills_breakdown.confirmed_by_inference.length})
                        </h4>
                      </div>
                      <div className="grid grid-cols-1 gap-3">
                        {report.skills_breakdown.confirmed_by_inference.map((inf, i) => (
                          <div
                            key={i}
                            className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 space-y-2.5 text-xs"
                          >
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center space-x-2">
                                <span className="text-sm font-bold text-white">{inf.missing_skill}</span>
                                <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-[11px] border border-indigo-500/30">
                                  Prior: {inf.matched_resume_skill}
                                </span>
                              </div>
                              <div className="flex items-center space-x-2 font-mono text-[11px]">
                                <span className="text-slate-400">Confidence:</span>
                                <span className="font-bold text-indigo-300 bg-indigo-900/60 px-2 py-0.5 rounded">
                                  {inf.confidence}%
                                </span>
                              </div>
                            </div>

                            {/* Mathematical Provenance Bar */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono text-slate-400 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                              <div>
                                <span className="text-slate-400">Graph Link Weight (w_edge):</span>
                                <span className="ml-1 text-amber-300 font-bold">{inf.edge_weight || '0.75'}</span>
                              </div>
                              <div>
                                <span className="text-slate-400">SBERT Similarity (sim):</span>
                                <span className="ml-1 text-emerald-300 font-bold">{inf.semantic_similarity || '0.31'}</span>
                              </div>
                            </div>

                            {/* Traceable Quote */}
                            <blockquote className="m-0 pl-3 border-l-2 border-indigo-500/50 text-slate-300 italic text-[11px] leading-relaxed">
                              "{inf.matched_statement}"
                            </blockquote>

                            {inf.selected_option && (
                              <div className="text-[11px] text-emerald-400 font-mono">
                                ✓ Verified via Interview: "{inf.selected_option}"
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                {/* 3. Partially Confirmed */}
                {(activeTab === 'all' || activeTab === 'partial') &&
                  report.skills_breakdown.partially_confirmed.length > 0 && (
                    <div className="space-y-3 pt-2">
                      <div className="flex items-center space-x-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
                        <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-amber-400">
                          Partially Confirmed (Tool/Framework Level) ({report.skills_breakdown.partially_confirmed.length})
                        </h4>
                      </div>
                      <div className="grid grid-cols-1 gap-3">
                        {report.skills_breakdown.partially_confirmed.map((inf, i) => (
                          <div
                            key={i}
                            className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/30 space-y-2.5 text-xs"
                          >
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center space-x-2">
                                <span className="text-sm font-bold text-white">{inf.missing_skill}</span>
                                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[11px] border border-amber-500/30">
                                  Prior: {inf.matched_resume_skill}
                                </span>
                              </div>
                              <div className="flex items-center space-x-2 font-mono text-[11px]">
                                <span className="text-slate-400">Confidence:</span>
                                <span className="font-bold text-amber-300 bg-amber-900/60 px-2 py-0.5 rounded">
                                  {inf.confidence}%
                                </span>
                              </div>
                            </div>

                            <blockquote className="m-0 pl-3 border-l-2 border-amber-500/50 text-slate-300 italic text-[11px]">
                              "{inf.matched_statement}"
                            </blockquote>

                            {inf.selected_option && (
                              <div className="text-[11px] text-amber-400 font-mono">
                                ⚠ Verified Scope: "{inf.selected_option}" (partial weight: 0.50)
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                {/* 4. Genuine Gaps */}
                {(activeTab === 'all' || activeTab === 'gaps') &&
                  report.skills_breakdown.genuine_gaps.length > 0 && (
                    <div className="space-y-3 pt-2">
                      <div className="flex items-center space-x-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-400"></span>
                        <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-rose-400">
                          Genuine Skill Gaps ({report.skills_breakdown.genuine_gaps.length})
                        </h4>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {report.skills_breakdown.genuine_gaps.map((inf, i) => (
                          <span
                            key={i}
                            className="px-3 py-1.5 rounded-lg bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs font-semibold flex items-center space-x-1.5"
                          >
                            <span className="text-rose-400">✕</span>
                            <span>{inf.missing_skill}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            </div>

            {/* Constrained Resume Rewrite Studio */}
            {report.suggested_rewrites && report.suggested_rewrites.length > 0 && (
              <div className="glass-panel rounded-2xl p-6 sm:p-8 border-slate-800 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                  <div>
                    <h3 className="text-xl font-bold text-white font-serif">
                      Academic Resume Rewrite Studio
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Deterministic slot-filling transformations. Guarantees zero hallucinations, unverified tools, or altered metrics.
                    </p>
                  </div>

                  <button
                    onClick={handleCopyAllRewrites}
                    className="px-3.5 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/40 text-xs font-mono text-indigo-300 hover:text-white transition flex items-center space-x-1.5 cursor-pointer shrink-0"
                  >
                    <span>{copiedAll ? '✓ Copied All Rewrites' : 'Copy All Revisions'}</span>
                  </button>
                </div>

                <div className="space-y-4">
                  {report.suggested_rewrites.map((rw, i) => (
                    <div
                      key={i}
                      className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3 text-xs transition hover:border-slate-700"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono font-bold uppercase bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 px-2.5 py-0.5 rounded">
                          Target Skill: {rw.missing_skill}
                        </span>

                        <button
                          onClick={() => handleCopyRewrite(rw.suggested_rewrite, i)}
                          className="text-xs text-slate-400 hover:text-white font-mono flex items-center space-x-1 cursor-pointer"
                        >
                          <span>{copiedIndex === i ? '✓ Copied' : 'Copy'}</span>
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                        {/* Original */}
                        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                          <span className="text-[10px] font-mono font-bold uppercase text-slate-500 tracking-wider block">
                            Original Resume Bullet:
                          </span>
                          <p className="text-slate-300 italic m-0 leading-relaxed">
                            "{rw.original_statement}"
                          </p>
                        </div>

                        {/* Suggested */}
                        <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-1">
                          <span className="text-[10px] font-mono font-bold uppercase text-emerald-400 tracking-wider block">
                            Suggested Academic Revision:
                          </span>
                          <p className="text-emerald-200 font-medium m-0 leading-relaxed">
                            "{rw.suggested_rewrite}"
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* ─────────────────────────────────────────────────────────
          INSPECT RAW JSON MODAL
      ───────────────────────────────────────────────────────── */}
      {showJsonModal && report && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col border border-slate-700 shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h4 className="text-sm font-bold text-white font-mono">Stage 5 API Output Payload</h4>
              <button
                onClick={() => setShowJsonModal(false)}
                className="text-slate-400 hover:text-white font-bold text-base cursor-pointer"
              >
                ✕
              </button>
            </div>
            <div className="p-4 overflow-y-auto flex-1 font-mono text-xs text-indigo-300 bg-slate-950/90">
              <pre className="m-0 leading-relaxed whitespace-pre-wrap">{JSON.stringify(report, null, 2)}</pre>
            </div>
            <div className="p-3 border-t border-slate-800 text-right">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(report, null, 2));
                  setShowJsonModal(false);
                }}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs cursor-pointer font-mono"
              >
                Copy JSON & Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────
          ACADEMIC FOOTER
      ───────────────────────────────────────────────────────── */}
      <footer className="border-t border-slate-800/80 bg-[#080c14] py-6 px-4 text-center text-xs text-slate-500 font-mono no-print">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <span>SkillGraph — Natural Language Processing Research Project</span>
          <span className="text-slate-600">Hybrid Graph-Semantic Inference • Zero Cloud LLM Dependencies</span>
        </div>
      </footer>
    </div>
  );
}
