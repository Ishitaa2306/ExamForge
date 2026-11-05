import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Send,
  CheckCircle,
  AlertTriangle,
  Clock,
  BookOpen,
  BarChart2,
  Sparkles,
  Layers,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { examApi } from '../services/api.js'

const DIFFICULTY_COLOR = {
  EASY: 'bg-sage/15 text-sage border-sage/20',
  MEDIUM: 'bg-olive/15 text-olive border-olive/20',
  HARD: 'bg-terracotta/15 text-terracotta border-terracotta/20',
}

const CATEGORY_COLOR = {
  DEFINITION: 'bg-sand text-charcoal border-sand',
  CONCEPTUAL: 'bg-sage/20 text-sage border-sage/30',
  DIFFERENCE: 'bg-lavender/25 text-lavender border-lavender/30',
  APPLICATION: 'bg-olive/20 text-olive border-olive/30',
  NUMERICAL: 'bg-terracotta/20 text-terracotta border-terracotta/30',
  ANALYTICAL: 'bg-rose/25 text-rose border-rose/30',
  SCENARIO: 'bg-sand/80 text-charcoal border-sand',
  TRICKY: 'bg-terracotta/25 text-terracotta border-terracotta/35 font-semibold',
}

export default function ExamSessionPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [question, setQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [complete, setComplete] = useState(false)
  const [examError, setExamError] = useState(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  const startTimeRef = useRef(null)
  const timerIntervalRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    startOrResume()
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current)
    }
  }, [id]) // eslint-disable-line

  // Start real-time elapsed counter for the active question
  function resetTimer() {
    startTimeRef.current = Date.now()
    setElapsedSeconds(0)
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current)
    timerIntervalRef.current = setInterval(() => {
      if (startTimeRef.current) {
        setElapsedSeconds(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }
    }, 1000)
  }

  async function startOrResume() {
    setLoading(true)
    try {
      const { data } = await examApi.start(id)
      if (data.is_last && data.question_asked_id === -1) {
        setComplete(true)
      } else {
        setQuestion(data)
        resetTimer()
      }
    } catch (err) {
      const detail = err.response?.data?.detail || ''
      if (detail.includes('already') || detail.includes('COMPLETED') || detail.includes('ABANDONED')) {
        setComplete(true)
      } else {
        setExamError(detail || 'Failed to start examination session.')
      }
    } finally {
      setLoading(false)
    }
  }

  async function submitAnswer(e) {
    e.preventDefault()
    if (!answer.trim() || submitting) return

    setSubmitting(true)
    const timeTaken = startTimeRef.current
      ? Math.round((Date.now() - startTimeRef.current) / 1000)
      : null

    try {
      const { data } = await examApi.answer(
        Number(id),
        question.question_asked_id,
        answer.trim(),
        timeTaken
      )
      setAnswer('')
      if (data.is_last && data.question_asked_id === -1) {
        setComplete(true)
        if (timerIntervalRef.current) clearInterval(timerIntervalRef.current)
        toast.success('Examination completed. Report synthesized!')
      } else {
        setQuestion(data)
        resetTimer()
        setTimeout(() => textareaRef.current?.focus(), 150)
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit answer. Please retry.')
    } finally {
      setSubmitting(false)
    }
  }

  async function abandonExam() {
    if (!confirm('Are you sure you want to abandon this examination? An incomplete record will be logged.')) return
    try {
      await examApi.abandon(id)
      toast('Examination session abandoned.')
      navigate('/examinations')
    } catch {
      navigate('/examinations')
    }
  }

  function formatTime(secs) {
    const mins = Math.floor(secs / 60)
    const rem = secs % 60
    return `${mins}:${rem < 10 ? '0' : ''}${rem}`
  }

  // ── Completion Screen ───────────────────────────────────────────────────────
  if (complete) {
    return (
      <div className="page-container flex flex-col items-center justify-center min-h-[75vh]">
        <div className="card text-center max-w-lg w-full p-10 bg-white border border-sand shadow-card rounded-2xl animate-slide-up">
          <div className="w-16 h-16 rounded-2xl bg-sage/20 text-sage flex items-center justify-center mx-auto mb-6 shadow-soft">
            <CheckCircle size={36} />
          </div>
          <h2 className="text-3xl font-display font-bold text-charcoal mb-3">Examination Complete</h2>
          <p className="text-warmgray text-sm leading-relaxed mb-8">
            Every submitted answer was semantically evaluated by IBM Granite.
            Google Gemini has compiled your comprehensive academic performance report.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => navigate('/examinations')}
              className="btn-secondary flex-1 text-sm py-3 justify-center"
            >
              Examination History
            </button>
            <button
              onClick={() => navigate(`/reports/${id}`)}
              className="btn-primary flex-1 text-sm py-3 justify-center shadow-soft hover:shadow-card"
            >
              <BarChart2 size={16} /> View Performance Report
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ── Error Screen ───────────────────────────────────────────────────────────
  if (examError) {
    return (
      <div className="page-container flex flex-col items-center justify-center min-h-[65vh]">
        <div className="card text-center max-w-md w-full p-8 bg-white border border-sand">
          <ShieldAlert className="mx-auto mb-4 text-terracotta" size={40} />
          <h2 className="text-xl font-display font-bold text-charcoal mb-2">Examination Unavailable</h2>
          <p className="text-warmgray text-sm mb-6">{examError}</p>
          <button onClick={() => navigate('/examinations')} className="btn-secondary w-full">
            Back to Examinations
          </button>
        </div>
      </div>
    )
  }

  // ── Loading Screen ─────────────────────────────────────────────────────────
  if (loading || !question) {
    return (
      <div className="page-container flex flex-col items-center justify-center min-h-[65vh]">
        <div className="card text-center w-full max-w-xl py-16 p-8 bg-white border border-sand shadow-soft">
          <div className="w-10 h-10 border-2 border-terracotta border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm font-semibold text-charcoal">Gemini Autonomous Examiner is preparing the session...</p>
          <p className="text-xs text-warmgray mt-1">Retrieving grounded curriculum context from ChromaDB.</p>
        </div>
      </div>
    )
  }

  const progressPct = question.progress_pct || 0
  const wordCount = answer.trim() ? answer.trim().split(/\s+/).length : 0

  return (
    <div className="page-container max-w-3xl animate-fade-in py-8">
      {/* Top Header Card */}
      <div className="flex items-center justify-between gap-4 mb-4">
        <div>
          <span className="text-xs font-semibold text-terracotta uppercase tracking-wider">
            Oral Academic Defense
          </span>
          <h1 className="text-2xl font-display font-bold text-charcoal">
            Examination Session #{id}
          </h1>
        </div>

        {/* Stopwatch Timer */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-ivory border border-sand text-xs font-semibold text-charcoal shadow-soft">
          <Clock size={14} className="text-terracotta animate-pulse" />
          <span>{formatTime(elapsedSeconds)}</span>
        </div>
      </div>

      {/* Progress Bar & Indicators */}
      <div className="card bg-white border border-sand p-4 mb-6 shadow-soft rounded-xl">
        <div className="flex items-center justify-between text-xs text-warmgray mb-2">
          <span>Question <strong>{question.order_index}</strong></span>
          <span className="font-semibold text-charcoal">{Math.round(progressPct)}% Completed</span>
        </div>
        <div className="w-full bg-sand/60 rounded-full h-2 overflow-hidden">
          <div
            className="bg-terracotta h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${Math.max(5, progressPct)}%` }}
          />
        </div>
      </div>

      {/* Question Card */}
      <div className="card bg-white border border-sand p-6 sm:p-8 mb-6 shadow-card rounded-2xl relative">
        {/* Badges Bar */}
        <div className="flex flex-wrap items-center gap-2 mb-4">
          {/* Follow-up question indicator */}
          {question.is_follow_up ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-lavender/30 text-charcoal border border-lavender/40">
              <Sparkles size={12} className="text-terracotta" />
              Follow-up Probe: Probing Reasoning
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-sand/80 text-charcoal">
              <Layers size={11} className="text-warmgray" />
              Curriculum Question
            </span>
          )}

          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${CATEGORY_COLOR[question.category] || 'bg-sand text-charcoal'}`}>
            {question.category}
          </span>

          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${DIFFICULTY_COLOR[question.difficulty] || 'bg-sand text-charcoal'}`}>
            {question.difficulty}
          </span>

          {question.topic_name && (
            <span className="ml-auto inline-flex items-center gap-1 text-xs font-medium text-warmgray">
              <BookOpen size={12} />
              {question.topic_name}
            </span>
          )}
        </div>

        {/* Primary Question Formulation */}
        <h2 className="text-xl sm:text-2xl font-serif text-charcoal leading-snug font-medium pt-1">
          {question.question_text}
        </h2>

        {question.is_follow_up && (
          <p className="text-xs text-warmgray mt-3 italic border-t border-sand/70 pt-2.5">
            The examiner has posed this question based on gaps detected in your previous response.
          </p>
        )}
      </div>

      {/* Answer Submission Form */}
      <form onSubmit={submitAnswer} className="space-y-4">
        <div className="card bg-white border border-sand p-6 shadow-card rounded-2xl">
          <div className="flex items-center justify-between mb-2">
            <label className="label text-sm font-semibold text-charcoal">Your Academic Explanation</label>
            <span className="text-xs text-warmgray">{wordCount} words</span>
          </div>

          <textarea
            ref={textareaRef}
            rows={8}
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Formulate your response thoroughly. Explain fundamental mechanisms, reasoning, and context. IBM Granite will semantically evaluate your depth of understanding..."
            className="input-field resize-none leading-relaxed text-base font-normal p-4"
            disabled={submitting}
            autoFocus
          />

          <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
            <button
              type="button"
              onClick={abandonExam}
              className="btn-ghost text-xs text-warmgray hover:text-terracotta"
            >
              Abandon Session
            </button>

            <button
              type="submit"
              disabled={submitting || !answer.trim()}
              className="btn-primary px-7 py-3 rounded-xl font-semibold shadow-soft hover:shadow-card disabled:opacity-50 transition-all w-full sm:w-auto"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>IBM Granite Evaluating...</span>
                </>
              ) : (
                <>
                  <Send size={15} />
                  <span>{question.is_last ? 'Submit Final Answer' : 'Submit Answer & Continue'}</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
