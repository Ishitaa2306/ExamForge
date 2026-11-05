import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Send, CheckCircle, AlertTriangle, Clock, BookOpen, BarChart2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { examApi } from '../services/api.js'

const DIFFICULTY_COLOR = {
  EASY:   'bg-sage/15 text-sage',
  MEDIUM: 'bg-olive/15 text-olive',
  HARD:   'bg-terracotta/15 text-terracotta',
}

const CATEGORY_COLOR = {
  DEFINITION:  'bg-lavender/15 text-lavender',
  CONCEPTUAL:  'bg-sage/15 text-sage',
  DIFFERENCE:  'bg-olive/15 text-olive',
  APPLICATION: 'bg-terracotta/15 text-terracotta',
  NUMERICAL:   'bg-charcoal/10 text-charcoal',
  ANALYTICAL:  'bg-lavender/15 text-lavender',
  SCENARIO:    'bg-rose/30 text-terracotta',
  TRICKY:      'bg-terracotta/20 text-terracotta',
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
  const startTimeRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    startOrResume()
  }, []) // eslint-disable-line

  async function startOrResume() {
    setLoading(true)
    try {
      const { data } = await examApi.start(id)
      if (data.is_last && data.question_asked_id === -1) {
        setComplete(true)
      } else {
        setQuestion(data)
        startTimeRef.current = Date.now()
      }
    } catch (err) {
      const detail = err.response?.data?.detail || ''
      if (detail.includes('already') || detail.includes('COMPLETED') || detail.includes('ABANDONED')) {
        setComplete(true)
      } else {
        setExamError(detail || 'Failed to start examination')
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
      const { data } = await examApi.answer(Number(id), question.question_asked_id, answer.trim(), timeTaken)
      setAnswer('')
      if (data.is_last && data.question_asked_id === -1) {
        // Examination completed by server
        setComplete(true)
        toast.success('Examination complete! Generating your report…')
      } else {
        setQuestion(data)
        startTimeRef.current = Date.now()
        // Focus textarea for next answer
        setTimeout(() => textareaRef.current?.focus(), 100)
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit answer')
    } finally {
      setSubmitting(false)
    }
  }

  async function abandonExam() {
    if (!confirm('Abandon this examination? You can start a new one any time.')) return
    try {
      await examApi.abandon(id)
      toast('Examination abandoned')
      navigate('/examinations')
    } catch {
      navigate('/examinations')
    }
  }

  // ── Completion screen ─────────────────────────────────────────────────────
  if (complete) {
    return (
      <div className="page-container flex flex-col items-center justify-center min-h-[70vh]">
        <div className="card text-center max-w-md w-full animate-slide-up">
          <div className="w-16 h-16 rounded-full bg-sage/20 flex items-center justify-center mx-auto mb-5">
            <CheckCircle className="text-sage" size={32} />
          </div>
          <h2 className="text-2xl font-display font-semibold text-charcoal mb-2">Examination Complete</h2>
          <p className="text-warmgray text-sm mb-6">
            Your answers have been evaluated. A detailed knowledge assessment report is being generated.
          </p>
          <div className="flex gap-3">
            <button onClick={() => navigate('/examinations')} className="btn-secondary flex-1 text-sm">
              All Examinations
            </button>
            <button onClick={() => navigate(`/reports/${id}`)} className="btn-primary flex-1 text-sm">
              <BarChart2 size={15} /> View Report
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ── Error screen ──────────────────────────────────────────────────────────
  if (examError) {
    return (
      <div className="page-container flex flex-col items-center justify-center min-h-[60vh]">
        <div className="card text-center max-w-md w-full">
          <AlertTriangle className="mx-auto mb-3 text-terracotta" size={36} />
          <h2 className="text-lg font-display font-semibold text-charcoal mb-2">Unable to start examination</h2>
          <p className="text-warmgray text-sm mb-5">{examError}</p>
          <button onClick={() => navigate('/examinations')} className="btn-secondary">Back to Examinations</button>
        </div>
      </div>
    )
  }

  // ── Loading ───────────────────────────────────────────────────────────────
  if (loading || !question) {
    return (
      <div className="page-container flex flex-col items-center justify-center min-h-[60vh]">
        <div className="card text-center w-full max-w-lg py-16 animate-pulse">
          <div className="h-4 bg-sand rounded w-1/4 mx-auto mb-3" />
          <div className="h-6 bg-sand rounded w-3/4 mx-auto mb-2" />
          <div className="h-6 bg-sand rounded w-2/3 mx-auto" />
          <p className="text-warmgray text-sm mt-8">Loading question…</p>
        </div>
      </div>
    )
  }

  const progressPct = question.progress_pct || 0

  // ── Main exam screen ──────────────────────────────────────────────────────
  return (
    <div className="page-container max-w-2xl animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-terracotta flex items-center justify-center">
              <BookOpen className="text-white" size={14} />
            </div>
            <span className="font-display font-semibold text-charcoal">Examination #{id}</span>
          </div>
          <span className="text-xs text-warmgray font-medium">{Math.round(progressPct)}% complete</span>
        </div>
        {/* Progress bar */}
        <div className="mt-3 bg-sand rounded-full h-1.5">
          <div
            className="bg-terracotta h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Question panel */}
      <div className="card mb-5 animate-slide-up">
        {/* Metadata */}
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${CATEGORY_COLOR[question.category] || 'bg-sand text-warmgray'}`}>
            {question.category}
          </span>
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${DIFFICULTY_COLOR[question.difficulty] || 'bg-sand text-warmgray'}`}>
            {question.difficulty}
          </span>
          {question.topic_name && (
            <span className="inline-flex items-center gap-1 text-xs text-warmgray">
              <BookOpen size={11} /> {question.topic_name}
            </span>
          )}
          <span className="ml-auto text-xs text-warmgray">Q{question.order_index}</span>
        </div>

        {/* Question text */}
        <p className="text-charcoal text-[1.05rem] leading-relaxed font-medium">
          {question.question_text}
        </p>
      </div>

      {/* Answer form */}
      <form onSubmit={submitAnswer} className="space-y-4">
        <div>
          <label className="label">Your Answer</label>
          <textarea
            ref={textareaRef}
            rows={7}
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Write a thorough answer demonstrating your understanding…"
            className="input-field resize-none leading-relaxed"
            disabled={submitting}
            autoFocus
          />
          <p className="text-xs text-warmgray mt-1 text-right">{answer.trim().split(/\s+/).filter(Boolean).length} words</p>
        </div>
        <div className="flex justify-between items-center gap-3">
          <button
            type="button"
            onClick={abandonExam}
            className="btn-ghost text-sm"
          >
            Abandon
          </button>
          <button
            type="submit"
            disabled={submitting || !answer.trim()}
            className="btn-primary"
          >
            <Send size={15} />
            {submitting ? 'Submitting…' : question.is_last ? 'Submit Final Answer' : 'Submit Answer'}
          </button>
        </div>
      </form>
    </div>
  )
}
