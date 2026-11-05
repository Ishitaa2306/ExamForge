import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, BookOpen, List, Layers, Brain, Play, RefreshCw, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { docsApi, examApi } from '../services/api.js'
import toast from 'react-hot-toast'

const STATUS_COLOR = {
  UPLOADED: 'badge-neutral',
  PROCESSING: 'badge bg-olive/20 text-olive',
  ANALYZED: 'badge-strong',
  FAILED: 'badge-weak',
}

const TYPE_COLOR = {
  DEFINITION: 'bg-lavender/15 text-lavender',
  FORMULA: 'bg-terracotta/15 text-terracotta',
  ALGORITHM: 'bg-sage/15 text-sage',
  CONCEPT: 'bg-olive/15 text-olive',
}

export default function DocumentDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [doc, setDoc] = useState(null)
  const [km, setKm] = useState(null)
  const [loading, setLoading] = useState(true)
  const [kmLoading, setKmLoading] = useState(false)
  const [expandedTopics, setExpandedTopics] = useState({})
  const [creatingExam, setCreatingExam] = useState(false)
  const [maxQ, setMaxQ] = useState(15)

  const loadDoc = useCallback(async () => {
    try {
      const { data } = await docsApi.status(id)
      setDoc(data)
      if (data.status === 'ANALYZED' && !km) loadKm()
    } catch (err) {
      toast.error('Document not found')
      navigate('/documents')
    } finally {
      setLoading(false)
    }
  }, [id]) // eslint-disable-line

  const loadKm = useCallback(async () => {
    setKmLoading(true)
    try {
      const { data } = await docsApi.knowledgeMap(id)
      setKm(data)
      const expanded = {}
      data.topics.forEach((t) => { expanded[t.id] = true })
      setExpandedTopics(expanded)
    } catch { /* not ready yet */ }
    finally { setKmLoading(false) }
  }, [id])

  useEffect(() => {
    loadDoc()
    // Poll if processing
    const poll = setInterval(() => {
      if (doc?.status === 'PROCESSING') loadDoc()
    }, 3000)
    return () => clearInterval(poll)
  }, []) // eslint-disable-line

  async function startExam() {
    if (doc?.status !== 'ANALYZED') {
      toast.error('Document must be analyzed before starting an examination')
      return
    }
    setCreatingExam(true)
    try {
      const { data } = await examApi.create(Number(id), maxQ)
      toast.success('Examination created!')
      navigate(`/examinations/${data.id}/session`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create examination')
    } finally {
      setCreatingExam(false)
    }
  }

  if (loading) return (
    <div className="page-container">
      <div className="card animate-pulse py-12 text-center text-warmgray">Loading document…</div>
    </div>
  )

  if (!doc) return null

  return (
    <div className="page-container animate-fade-in">
      {/* Back */}
      <Link to="/documents" className="btn-ghost mb-6 -ml-2 text-sm">
        <ArrowLeft size={15} /> Back to documents
      </Link>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="section-title break-all">{doc.original_filename || `Document ${id}`}</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className={STATUS_COLOR[doc.status] || 'badge-neutral'}>{doc.status}</span>
            {doc.page_count && <span className="text-xs text-warmgray">{doc.page_count} pages</span>}
            {doc.word_count && <span className="text-xs text-warmgray">{doc.word_count?.toLocaleString()} words</span>}
            {doc.topic_count > 0 && <span className="text-xs text-warmgray">{doc.topic_count} topics</span>}
            {doc.question_count > 0 && <span className="text-xs text-warmgray">{doc.question_count} questions</span>}
          </div>
        </div>
        {doc.status === 'ANALYZED' && (
          <div className="flex flex-wrap items-center gap-2 flex-shrink-0">
            <Link
              to={`/documents/${id}/questions`}
              className="btn-secondary text-sm inline-flex items-center gap-1.5"
            >
              <List size={15} /> Question Bank
            </Link>
            <select
              value={maxQ}
              onChange={(e) => setMaxQ(Number(e.target.value))}
              className="input-field text-sm py-2 w-32"
            >
              {[5, 10, 15, 20, 25, 30].map((n) => (
                <option key={n} value={n}>{n} questions</option>
              ))}
            </select>
            <button onClick={startExam} disabled={creatingExam} className="btn-primary">
              <Play size={16} /> {creatingExam ? 'Creating…' : 'Start Examination'}
            </button>
          </div>
        )}
        {doc.status === 'FAILED' && (
          <button onClick={() => docsApi.analyze(id).then(loadDoc)} className="btn-secondary">
            <RefreshCw size={15} /> Retry Analysis
          </button>
        )}
      </div>

      {/* Processing state */}
      {doc.status === 'PROCESSING' && (
        <div className="card mb-6 flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-olive/20 flex items-center justify-center">
            <RefreshCw className="text-olive animate-spin" size={20} />
          </div>
          <div>
            <p className="font-medium text-charcoal">Analysis in progress…</p>
            <p className="text-sm text-warmgray">Extracting topics, concepts and generating questions. This takes 10–30 seconds.</p>
          </div>
        </div>
      )}

      {/* Knowledge Map */}
      {doc.status === 'ANALYZED' && (
        <>
          {kmLoading ? (
            <div className="card animate-pulse text-center py-8 text-warmgray">Loading knowledge map…</div>
          ) : km ? (
            <div className="space-y-4">
              {/* Summary row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { icon: BookOpen, label: 'Topics', value: km.total_topics, color: 'text-terracotta' },
                  { icon: Layers, label: 'Subtopics', value: km.total_subtopics, color: 'text-sage' },
                  { icon: Brain, label: 'Concepts', value: km.total_concepts, color: 'text-lavender' },
                  { icon: List, label: 'Questions', value: km.total_questions, color: 'text-olive' },
                ].map(({ icon: Icon, label, value, color }) => (
                  <div key={label} className="card py-4 text-center">
                    <Icon className={`mx-auto mb-1 ${color}`} size={20} />
                    <p className="text-xl font-bold font-display text-charcoal">{value}</p>
                    <p className="text-xs text-warmgray">{label}</p>
                  </div>
                ))}
              </div>

              {/* Topics */}
              <div className="space-y-3">
                {km.topics.map((topic) => (
                  <div key={topic.id} className="card p-0 overflow-hidden">
                    <button
                      className="w-full flex items-center justify-between px-5 py-4 hover:bg-ivory/50 transition-colors"
                      onClick={() => setExpandedTopics((prev) => ({ ...prev, [topic.id]: !prev[topic.id] }))}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-7 h-7 rounded-md bg-terracotta/10 flex items-center justify-center">
                          <BookOpen className="text-terracotta" size={14} />
                        </div>
                        <div className="text-left">
                          <p className="font-medium text-charcoal text-sm">{topic.name}</p>
                          {topic.description && <p className="text-xs text-warmgray mt-0.5">{topic.description}</p>}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-warmgray">{topic.question_count} Q</span>
                        {expandedTopics[topic.id] ? <ChevronUp size={15} className="text-warmgray" /> : <ChevronDown size={15} className="text-warmgray" />}
                      </div>
                    </button>
                    {expandedTopics[topic.id] && (topic.subtopics?.length > 0 || topic.direct_concepts?.length > 0) && (
                      <div className="border-t border-sand px-5 py-4 space-y-4">
                        {topic.subtopics?.map((st) => (
                          <div key={st.id}>
                            <p className="text-xs font-semibold text-warmgray uppercase tracking-wide mb-2">{st.name}</p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                              {st.concepts?.map((c) => (
                                <div key={c.id} className="bg-ivory rounded-lg p-3">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${TYPE_COLOR[c.type] || 'bg-sand text-warmgray'}`}>
                                      {c.type}
                                    </span>
                                    <span className="text-xs font-medium text-charcoal">{c.name}</span>
                                  </div>
                                  <p className="text-xs text-warmgray leading-relaxed">{c.content?.slice(0, 120)}{c.content?.length > 120 ? '…' : ''}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="card text-center py-8">
              <p className="text-warmgray">Knowledge map not available.</p>
              <button onClick={loadKm} className="btn-secondary mt-3">Load Knowledge Map</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
