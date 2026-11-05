import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Compass,
  Search,
  Filter,
  FileText,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Tag,
  CheckCircle,
  HelpCircle,
  Play,
} from 'lucide-react'
import { docsApi, questionsApi } from '../services/api.js'
import toast from 'react-hot-toast'

export default function QuestionBankPage() {
  const [documents, setDocuments] = useState([])
  const [selectedDocId, setSelectedDocId] = useState(null)
  const [questions, setQuestions] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [difficultyFilter, setDifficultyFilter] = useState('')
  const [expandedId, setExpandedId] = useState(null)

  const [topicMap, setTopicMap] = useState({})

  // Load available documents
  useEffect(() => {
    async function loadDocs() {
      try {
        const { data } = await docsApi.list(0, 50)
        const analyzed = (data.documents || []).filter((d) => d.status === 'ANALYZED')
        setDocuments(analyzed)
        if (analyzed.length > 0) {
          setSelectedDocId(analyzed[0].id)
        }
      } catch (err) {
        toast.error('Failed to load documents.')
      } finally {
        setLoading(false)
      }
    }
    loadDocs()
  }, [])

  // Load topic map whenever selected document changes
  useEffect(() => {
    if (!selectedDocId) return
    docsApi.knowledgeMap(selectedDocId)
      .then((res) => {
        const map = {}
        if (res.data?.topics) {
          res.data.topics.forEach((t) => { map[t.id] = t.name })
        }
        setTopicMap(map)
      })
      .catch(() => setTopicMap({}))
  }, [selectedDocId])

  // Load questions for selected document
  const loadQuestions = useCallback(async () => {
    if (!selectedDocId) return
    setLoading(true)
    try {
      const params = {}
      if (categoryFilter) params.category = categoryFilter
      if (difficultyFilter) params.difficulty = difficultyFilter

      const { data } = await questionsApi.bank(selectedDocId, params)
      setQuestions(data.questions || [])
      setTotal(data.total || 0)
    } catch (err) {
      toast.error('Failed to load questions from repository.')
    } finally {
      setLoading(false)
    }
  }, [selectedDocId, categoryFilter, difficultyFilter])

  useEffect(() => {
    loadQuestions()
  }, [loadQuestions])

  const filteredQuestions = questions.filter((q) => {
    if (!searchTerm) return true
    const term = searchTerm.toLowerCase()
    return (
      q.question_text.toLowerCase().includes(term) ||
      (q.category && q.category.toLowerCase().includes(term))
    )
  })

  // Group by topic
  const groupedQuestions = filteredQuestions.reduce((acc, q) => {
    const key = q.topic_id ? (topicMap[q.topic_id] || `Topic #${q.topic_id}`) : 'General Curriculum'
    if (!acc[key]) acc[key] = []
    acc[key].push(q)
    return acc
  }, {})

  const categoryBadgeColor = {
    DEFINITION: 'bg-sand text-charcoal',
    CONCEPTUAL: 'bg-sage/20 text-sage',
    DIFFERENCE: 'bg-lavender/25 text-lavender',
    APPLICATION: 'bg-olive/20 text-olive',
    NUMERICAL: 'bg-terracotta/20 text-terracotta',
    ANALYTICAL: 'bg-rose/25 text-rose',
    SCENARIO: 'bg-sand/80 text-charcoal',
    TRICKY: 'bg-terracotta/25 text-terracotta font-semibold',
  }

  const difficultyBadgeColor = {
    EASY: 'bg-sage/15 text-sage',
    MEDIUM: 'bg-olive/20 text-olive',
    HARD: 'bg-terracotta/20 text-terracotta font-semibold',
  }

  return (
    <div className="page-container animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-terracotta mb-1">
            <Compass className="w-4 h-4" />
            Curriculum Question Repository
          </div>
          <h1 className="section-title">Academic Question Bank</h1>
          <p className="text-sm text-warmgray mt-1">
            Explore Gemini-authored questions grounded in your syllabus and verified by IBM Granite.
          </p>
        </div>

        {selectedDocId && (
          <Link
            to="/examinations"
            className="btn-primary self-start text-sm shadow-soft hover:shadow-card transition-all"
          >
            <Play className="w-4 h-4" />
            Start Examination on Document
          </Link>
        )}
      </div>

      {/* Document Selector & Filter Bar */}
      <div className="card bg-white border border-sand p-5 mb-8 shadow-soft">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
          {/* Document Select */}
          <div className="md:col-span-1">
            <label className="label text-xs">Source Academic Document</label>
            <select
              value={selectedDocId || ''}
              onChange={(e) => setSelectedDocId(Number(e.target.value))}
              className="input-field text-sm py-2"
              disabled={documents.length === 0}
            >
              {documents.length === 0 ? (
                <option value="">No analyzed documents</option>
              ) : (
                documents.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.original_filename}
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Search Term */}
          <div className="md:col-span-1">
            <label className="label text-xs">Search Question Text</label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-warmgray" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search keywords..."
                className="input-field pl-9 text-sm py-2"
              />
            </div>
          </div>

          {/* Category Filter */}
          <div className="md:col-span-1">
            <label className="label text-xs">Cognitive Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="input-field text-sm py-2"
            >
              <option value="">All Categories (8)</option>
              <option value="CONCEPTUAL">Conceptual</option>
              <option value="DEFINITION">Definition</option>
              <option value="DIFFERENCE">Difference / Comparison</option>
              <option value="APPLICATION">Application</option>
              <option value="NUMERICAL">Numerical</option>
              <option value="ANALYTICAL">Analytical</option>
              <option value="SCENARIO">Scenario-based</option>
              <option value="TRICKY">Tricky / Misconception</option>
            </select>
          </div>

          {/* Difficulty Filter */}
          <div className="md:col-span-1">
            <label className="label text-xs">Difficulty Tier</label>
            <select
              value={difficultyFilter}
              onChange={(e) => setDifficultyFilter(e.target.value)}
              className="input-field text-sm py-2"
            >
              <option value="">All Difficulties</option>
              <option value="EASY">Easy</option>
              <option value="MEDIUM">Medium</option>
              <option value="HARD">Hard</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="card p-12 text-center bg-white border border-sand">
          <p className="text-sm text-warmgray">Loading question repository...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="card p-12 text-center bg-white border border-sand">
          <BookOpen className="w-12 h-12 text-sand mx-auto mb-3" />
          <h3 className="font-display text-lg font-bold text-charcoal mb-1">No Documents Analyzed Yet</h3>
          <p className="text-sm text-warmgray mb-6">
            Upload an academic syllabus or study material to automatically author grounded question banks.
          </p>
          <Link to="/documents" className="btn-primary text-sm inline-flex">
            Upload PDF Document
          </Link>
        </div>
      ) : filteredQuestions.length === 0 ? (
        <div className="card p-12 text-center bg-white border border-sand">
          <HelpCircle className="w-12 h-12 text-sand mx-auto mb-3" />
          <h3 className="font-display text-lg font-bold text-charcoal mb-1">No Questions Match Filter</h3>
          <p className="text-sm text-warmgray">Try adjusting your category or difficulty filters.</p>
        </div>
      ) : (
        <div className="space-y-8">
          <div className="flex items-center justify-between text-xs text-warmgray px-1">
            <span>
              Displaying <strong>{filteredQuestions.length}</strong> of <strong>{total}</strong> questions
            </span>
            <span>Grounded in active academic syllabus</span>
          </div>

          {Object.entries(groupedQuestions).map(([topicGroup, qList]) => (
            <div key={topicGroup} className="space-y-3">
              <div className="flex items-center gap-2 border-b border-sand pb-2">
                <Tag className="w-4 h-4 text-terracotta" />
                <h2 className="text-base font-bold font-display text-charcoal">{topicGroup}</h2>
                <span className="text-xs text-warmgray font-medium">({qList.length} questions)</span>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {qList.map((q) => {
                  const isExpanded = expandedId === q.id
                  return (
                    <div
                      key={q.id}
                      className="card bg-white border border-sand p-5 rounded-xl hover:shadow-soft transition-all"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            <span className={`badge ${categoryBadgeColor[q.category] || 'bg-sand text-charcoal'}`}>
                              {q.category}
                            </span>
                            <span className={`badge ${difficultyBadgeColor[q.difficulty] || 'bg-sand text-charcoal'}`}>
                              {q.difficulty}
                            </span>
                            {q.source_pages && q.source_pages.length > 0 && (
                              <span className="text-[11px] text-warmgray font-medium">
                                Pages: {q.source_pages.join(', ')}
                              </span>
                            )}
                          </div>
                          <p className="text-base font-medium text-charcoal leading-relaxed">{q.question_text}</p>
                        </div>

                        <button
                          onClick={() => setExpandedId(isExpanded ? null : q.id)}
                          className="p-1.5 rounded-lg text-warmgray hover:bg-ivory hover:text-charcoal transition-colors flex-shrink-0"
                          title="View evaluation rubric & expected points"
                        >
                          {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                        </button>
                      </div>

                      {/* Expandable Expected Points & Rubric */}
                      {isExpanded && (
                        <div className="mt-4 pt-4 border-t border-sand bg-ivory/40 -mx-5 -mb-5 p-5 rounded-b-xl space-y-3 text-xs">
                          {q.expected_answer_points && q.expected_answer_points.length > 0 && (
                            <div>
                              <strong className="text-charcoal block mb-1 font-semibold">
                                Expected Core Concepts:
                              </strong>
                              <ul className="list-disc list-inside space-y-1 text-charcoal/80 pl-1">
                                {q.expected_answer_points.map((pt, i) => (
                                  <li key={i}>{pt}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {q.evaluation_rubric && (
                            <div>
                              <strong className="text-charcoal block mb-1 font-semibold">
                                Scoring Rubric Guidance:
                              </strong>
                              <p className="text-warmgray">
                                {typeof q.evaluation_rubric === 'object'
                                  ? JSON.stringify(q.evaluation_rubric, null, 2)
                                  : q.evaluation_rubric}
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

