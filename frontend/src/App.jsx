import React, { useState } from 'react';

export default function App() {
  // Screen stages: 'upload' | 'questions' | 'report'
  const [screen, setScreen] = useState('upload');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Upload Form State
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState(
    'Senior Backend Engineer: Strong proficiency in Python (FastAPI, Django), PostgreSQL, MySQL, Redis, Docker, Kubernetes, microservices, distributed systems, ETL, Kafka, RabbitMQ, AWS.'
  );

  // Session & Questions State
  const [sessionId, setSessionId] = useState(null);
  const [explicitlyMatched, setExplicitlyMatched] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  // Final Report State
  const [report, setReport] = useState(null);

  // ─────────────────────────────────────────────────────────────
  // 1. Handle Resume Analysis (Upload Screen)
  // ─────────────────────────────────────────────────────────────
  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a resume file (.docx or .pdf)');
      return;
    }
    if (!jobDescription.trim()) {
      setError('Please provide a job description');
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
        throw new Error(data.error || 'Failed to analyze resume');
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
        // Fallback: fetch report directly
        await fetchReport(data.session_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ─────────────────────────────────────────────────────────────
  // 2. Handle Clarifying Question Answer
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
        throw new Error(data.error || 'Failed to submit response');
      }

      const nextIndex = currentQuestionIndex + 1;
      if (nextIndex < questions.length) {
        setCurrentQuestionIndex(nextIndex);
      } else {
        // All questions completed -> fetch final report
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
        throw new Error(data.error || 'Failed to fetch report');
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
    setSessionId(null);
    setQuestions([]);
    setCurrentQuestionIndex(0);
    setReport(null);
    setError(null);
  };

  // ─────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 shadow-xs">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg">
              SG
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-800 m-0">SkillGraph</h1>
              <p className="text-xs text-slate-500 m-0">Explainable Implicit Skill Inference & Fit Analysis</p>
            </div>
          </div>
          {screen !== 'upload' && (
            <button
              onClick={handleReset}
              className="text-xs font-medium text-slate-600 hover:text-indigo-600 bg-slate-100 px-3 py-1.5 rounded-md transition"
            >
              Start New Analysis
            </button>
          )}
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-6 md:py-10">
        {error && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-sm flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-rose-500 font-bold ml-4">
              ✕
            </button>
          </div>
        )}

        {/* ── SCREEN 1: UPLOAD & INPUT ── */}
        {screen === 'upload' && (
          <div className="bg-white rounded-xl shadow-xs border border-slate-200 p-6 md:p-8">
            <div className="mb-6 border-b border-slate-100 pb-4">
              <h2 className="text-xl font-semibold text-slate-800">Analyze Candidate Resume</h2>
              <p className="text-sm text-slate-500">
                Upload your resume (.docx or .pdf) and paste the target job description to detect explicit skills and infer implicit knowledge.
              </p>
            </div>

            <form onSubmit={handleAnalyze} className="space-y-6">
              {/* File upload */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Resume File <span className="text-rose-500">*</span>
                </label>
                <div className="flex items-center space-x-3">
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={(e) => setFile(e.target.files[0] || null)}
                    className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer border border-slate-200 rounded-lg p-2"
                  />
                </div>
                {file && (
                  <p className="mt-1 text-xs text-emerald-600">Selected: {file.name}</p>
                )}
              </div>

              {/* Job description */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Job Description <span className="text-rose-500">*</span>
                </label>
                <textarea
                  rows={5}
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste target job requirements and qualifications here..."
                  className="w-full p-3 border border-slate-200 rounded-lg text-sm text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-transparent font-mono"
                />
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium rounded-lg shadow-xs transition flex items-center justify-center space-x-2 text-sm cursor-pointer"
              >
                {loading ? (
                  <span>Running NLP Pipeline (Stages 1–3)...</span>
                ) : (
                  <span>Analyze Resume & Skills</span>
                )}
              </button>
            </form>
          </div>
        )}

        {/* ── SCREEN 2: CLARIFYING QUESTIONS (CHAT-STYLE CARD) ── */}
        {screen === 'questions' && questions.length > 0 && (
          <div className="max-w-2xl mx-auto space-y-6">
            {/* Progress Indicator */}
            <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Clarifying Question {currentQuestionIndex + 1} of {questions.length}</span>
              <span>{Math.round(((currentQuestionIndex) / questions.length) * 100)}% Answered</span>
            </div>
            <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-indigo-600 h-full transition-all duration-300"
                style={{ width: `${((currentQuestionIndex) / questions.length) * 100}%` }}
              />
            </div>

            {/* Chat Card */}
            <div className="bg-white rounded-xl shadow-xs border border-slate-200 p-6 md:p-8 space-y-6">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center shrink-0 text-sm">
                  Q
                </div>
                <div className="flex-1">
                  <div className="inline-block bg-slate-100 text-indigo-900 font-semibold px-2.5 py-0.5 rounded text-xs mb-2">
                    Inference for: {questions[currentQuestionIndex].missing_skill}
                  </div>
                  <h3 className="text-base md:text-lg font-medium text-slate-800 leading-snug">
                    {questions[currentQuestionIndex].question}
                  </h3>
                </div>
              </div>

              {/* Options */}
              <div className="space-y-3 pt-2">
                <p className="text-xs font-medium uppercase text-slate-400 tracking-wider">
                  Select your experience level:
                </p>
                {questions[currentQuestionIndex].options.map((option, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSelectOption(option)}
                    disabled={loading}
                    className="w-full text-left p-3.5 rounded-lg border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/50 text-slate-700 hover:text-indigo-900 text-sm font-medium transition cursor-pointer flex items-center justify-between group"
                  >
                    <span>{option}</span>
                    <span className="text-slate-300 group-hover:text-indigo-500 font-bold">→</span>
                  </button>
                ))}
              </div>
            </div>

            <p className="text-xs text-center text-slate-400">
              Your response updates inference confidence and refines candidate fit without unverified assumptions.
            </p>
          </div>
        )}

        {/* ── SCREEN 3: FINAL FIT REPORT & REWRITES ── */}
        {screen === 'report' && report && (
          <div className="space-y-8">
            {/* Top Score Banner */}
            <div className="bg-white rounded-xl shadow-xs border border-slate-200 p-6 md:p-8 flex flex-col md:flex-row items-center justify-between gap-6">
              <div>
                <h2 className="text-2xl font-bold text-slate-800 m-0">Candidate Fit Report</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Matched {report.fit_summary.matched_count} of {report.fit_summary.total_required_skills} required skills from the job description.
                </p>
              </div>
              <div className="flex items-center space-x-4 bg-slate-50 border border-slate-200 px-6 py-4 rounded-xl">
                <div className="text-center">
                  <div className="text-3xl font-extrabold text-indigo-600">
                    {report.fit_summary.fit_percentage}%
                  </div>
                  <div className="text-xs uppercase tracking-wider font-semibold text-slate-500 mt-0.5">
                    Fit Percentage
                  </div>
                </div>
              </div>
            </div>

            {/* Skills Breakdown by Category */}
            <div className="bg-white rounded-xl shadow-xs border border-slate-200 p-6 md:p-8 space-y-6">
              <h3 className="text-lg font-bold text-slate-800 border-b border-slate-100 pb-3">
                Skills Classification Breakdown
              </h3>

              {/* 1. Explicitly Present */}
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                  <h4 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                    Explicitly Stated in Resume ({report.skills_breakdown.explicitly_present.length})
                  </h4>
                </div>
                <div className="flex flex-wrap gap-2">
                  {report.skills_breakdown.explicitly_present.map((skill, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-md text-xs font-medium"
                    >
                      ✓ {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* 2. Confirmed by Verification */}
              {report.skills_breakdown.confirmed_by_inference.length > 0 && (
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span>
                    <h4 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                      Confirmed Through Inference & Verification ({report.skills_breakdown.confirmed_by_inference.length})
                    </h4>
                  </div>
                  <div className="space-y-2">
                    {report.skills_breakdown.confirmed_by_inference.map((inf, i) => (
                      <div key={i} className="p-3 bg-indigo-50/50 border border-indigo-100 rounded-lg text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-indigo-900 text-sm">{inf.missing_skill}</span>
                          <span className="bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded font-semibold">
                            Confidence: {inf.confidence}%
                          </span>
                        </div>
                        <p className="text-slate-600 m-0">{inf.reasoning}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 3. Partially Confirmed */}
              {report.skills_breakdown.partially_confirmed.length > 0 && (
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                    <h4 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                      Partially Confirmed (Tool/Framework Level) ({report.skills_breakdown.partially_confirmed.length})
                    </h4>
                  </div>
                  <div className="space-y-2">
                    {report.skills_breakdown.partially_confirmed.map((inf, i) => (
                      <div key={i} className="p-3 bg-amber-50/50 border border-amber-100 rounded-lg text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-amber-900 text-sm">{inf.missing_skill}</span>
                          <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-semibold">
                            Confidence: {inf.confidence}%
                          </span>
                        </div>
                        <p className="text-slate-600 m-0">{inf.reasoning}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 4. Genuine Gaps */}
              {report.skills_breakdown.genuine_gaps.length > 0 && (
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                    <h4 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                      Genuine Skill Gaps ({report.skills_breakdown.genuine_gaps.length})
                    </h4>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {report.skills_breakdown.genuine_gaps.map((inf, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-rose-50 border border-rose-200 text-rose-800 rounded-md text-xs font-medium"
                      >
                        ✕ {inf.missing_skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Suggested Rewrites */}
            {report.suggested_rewrites && report.suggested_rewrites.length > 0 && (
              <div className="bg-white rounded-xl shadow-xs border border-slate-200 p-6 md:p-8 space-y-4">
                <div className="border-b border-slate-100 pb-3">
                  <h3 className="text-lg font-bold text-slate-800">
                    Constrained Resume Rewrite Suggestions
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Academic Honesty Guarantee: Rewrites strictly preserve verified context without hallucinating metrics or unconfirmed details.
                  </p>
                </div>

                <div className="space-y-4 pt-2">
                  {report.suggested_rewrites.map((rw, i) => (
                    <div key={i} className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-2 text-xs">
                      <div className="font-semibold text-indigo-700 uppercase tracking-wider">
                        Target Skill: {rw.missing_skill}
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="p-3 bg-white border border-slate-200 rounded-md">
                          <span className="font-bold text-slate-400 block mb-1 uppercase tracking-wider text-[10px]">
                            Original Resume Bullet:
                          </span>
                          <p className="text-slate-600 italic">"{rw.original_statement}"</p>
                        </div>
                        <div className="p-3 bg-emerald-50/50 border border-emerald-200 rounded-md">
                          <span className="font-bold text-emerald-700 block mb-1 uppercase tracking-wider text-[10px]">
                            Suggested Revision:
                          </span>
                          <p className="text-emerald-900 font-medium">"{rw.suggested_rewrite}"</p>
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

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 px-6 text-center text-xs text-slate-400">
        SkillGraph — NLP Pipeline for Inferring Implicit Skills in Resumes (Stage 6 Functional Demo)
      </footer>
    </div>
  );
}
