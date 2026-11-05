import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { ClipboardList, Plus, BarChart3, Clock, CheckCircle, X, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { examApi, docsApi } from '../services/api.js'

const STATUS_CONFIG = {
  CREATED:     { badge: 'badge-neutral',   label: 'Created' },
  IN_PROGRESS: { badge: 'badge bg-olive/20 text-olive', label: 'In Progress' },
  COMPLETED:   { badge: 'badge-strong',    label: 'Completed' },
  ABANDONED:   { badge: 'badge-weak',      label: 'Abandoned' },
}

export default function ExaminationsPage() {
  const navigate = useNavigate()
  const [examinations, setExaminations] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [docs, setDocs] = useState([])
  const [selectedDoc, setSelectedDoc] = useState('')
  const [maxQ, setMaxQ] = useState(15)
  const [creating, setCreating] = useState(false)

  const fetchExams = useCallback(async () => {
    try {
      const { data } = await examApi.list()
      setExaminations(data.examinations)
      setTotal(data.total)
    } catch {
      toast.error('Failed to load examinations')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchExams()
    docsApi.list(0, 50).then(({ data }) => {
      const analyzed = (data.documents || []).filter((d) => d.status === 'ANALYZED')
      setDocs(analyzed)
    }).catch(() => {})
  }, [fetchExams])

  async function createExam() {
    if (!selectedDoc) { toast.error('Select a document'); return }
    setCreating(true)
    try {
      const { data } = await examApi.create(Number(selectedDoc), maxQ)
      toast.success('Examination created!')
      setShowCreate(false)
      navigate(`/examinations/${data.id}/session`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create examination')
    } finally {
      setCreating(false)
    }
  }

  const fmtDate = (d) => d ? new Date(d).toLocaleDateString() : '—'
  const progressPct = (e) => Math.round((e.questions_asked_count / e.max_questions) * 100)

  return (
    <div className="page-container animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="section-title">Examinations</h1>
          <p className="text-warmgray text-sm mt-0.5">
            {loading ? 'Loading…' : `${total} examination${total !== 1 ? 's' : ''}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchExams} className="btn-ghost text-sm">
            <RefreshCw size={15} />
          </button>
          <button onClick={() => setShowCreate(true)} className="btn-primary text-sm">
            <Plus size={15} /> New Examination
          </button>
        </div>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-charcoal/30 backdrop-blur-sm z-50 flex items-center justify-center px-4">
          <div className="bg-white rounded-2xl shadow-raised w-full max-w-md p-6 animate-slide-up">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-display font-semibold text-charcoal">New Examination</h2>
              <button onClick={() => setShowCreate(false)} className="p-1.5 rounded-md text-warmgray hover:bg-sand transition-colors">
                <X size={16} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Study Document</label>
                {docs.length === 0 ? (
                  <p className="text-sm text-warmgray bg-ivory rounded-lg p-3">
                    No analyzed documents found. Upload and analyze a PDF first.
                  </p>
                ) : (
                  <select
                    value={selectedDoc}
                    onChange={(e) => setSelectedDoc(e.target.value)}
                    className="input-field"
                  >
                    <option value="">Select a document…</option>
                    {docs.map((d) => (
                      <option key={d.id} value={d.id}>{d.original_filename}</option>
                    ))}
                  </select>
                )}
              </div>
              <div>
                <label className="label">Maximum Questions</label>
                <select value={maxQ} onChange={(e) => setMaxQ(Number(e.target.value))} className="input-field">
                  {[5, 10, 15, 20, 25, 30].map((n) => (
                    <option key={n} value={n}>{n} questions</option>
                  ))}
                </select>
              </div>
              <p className="text-xs text-warmgray bg-ivory rounded-lg p-3">
                ExamForge will conduct an adaptive examination covering all major topics in your document. Difficulty adjusts based on your performance.
              </p>
            </div>

            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowCreate(false)} className="btn-secondary flex-1">Cancel</button>
              <button onClick={createExam} disabled={creating || !selectedDoc} className="btn-primary flex-1">
                {creating ? 'Creating…' : 'Start Examination'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse py-6 flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-sand" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-sand rounded w-1/3" />
                <div className="h-3 bg-sand rounded w-1/4" />
              </div>
            </div>
          ))}
        </div>
      ) : examinations.length === 0 ? (
        <div className="card text-center py-16">
          <ClipboardList className="mx-auto mb-3 text-sand" size={40} />
          <p className="font-medium text-charcoal">No examinations yet</p>
          <p className="text-warmgray text-sm mt-1 mb-5">Create your first examination to start assessing your knowledge.</p>
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus size={15} /> New Examination
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {examinations.map((exam) => {
            const cfg = STATUS_CONFIG[exam.status] || STATUS_CONFIG.CREATED
            const pct = progressPct(exam)
            return (
              <div key={exam.id} className="card">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-sage/10 flex items-center justify-center flex-shrink-0">
                    <ClipboardList className="text-sage" size={18} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium text-charcoal">Examination #{exam.id}</p>
                      <span className={cfg.badge}>{cfg.label}</span>
                    </div>
                    <p className="text-xs text-warmgray">
                      {exam.questions_asked_count}/{exam.max_questions} questions
                      {exam.current_difficulty && ` · ${exam.current_difficulty}`}
                      {exam.started_at && ` · Started ${fmtDate(exam.started_at)}`}
                    </p>
                    {/* Progress bar */}
                    <div className="mt-2 bg-sand rounded-full h-1.5 w-full max-w-xs">
                      <div
                        className="bg-terracotta h-1.5 rounded-full transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {exam.status === 'IN_PROGRESS' && (
                      <button
                        onClick={() => navigate(`/examinations/${exam.id}/session`)}
                        className="btn-primary text-sm py-1.5 px-3"
                      >
                        Resume
                      </button>
                    )}
                    {exam.status === 'COMPLETED' && (
                      <button
                        onClick={() => navigate(`/reports/${exam.id}`)}
                        className="btn-secondary text-sm py-1.5 px-3"
                      >
                        <BarChart3 size={14} /> Report
                      </button>
                    )}
                    {exam.status === 'CREATED' && (
                      <button
                        onClick={() => navigate(`/examinations/${exam.id}/session`)}
                        className="btn-primary text-sm py-1.5 px-3"
                      >
                        Start
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
