import { useEffect, useState, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FileText, ClipboardList, BarChart3, ArrowRight, Plus, TrendingUp, Clock } from 'lucide-react'
import { docsApi, examApi, reportsApi } from '../services/api.js'
import { useAuthStore } from '../store/authStore.js'

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [stats, setStats] = useState({ documents: 0, examinations: 0, reports: 0 })
  const [recentDocs, setRecentDocs] = useState([])
  const [recentExams, setRecentExams] = useState([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const [docs, exams, reports] = await Promise.all([
        docsApi.list(0, 3),
        examApi.list(0, 5),
        reportsApi.list(0, 5),
      ])
      setStats({
        documents: docs.data.total,
        examinations: exams.data.total,
        reports: reports.data.length,
      })
      setRecentDocs(docs.data.documents || [])
      setRecentExams(exams.data.examinations || [])
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const statCards = [
    { icon: FileText, label: 'Documents', value: stats.documents, to: '/documents', color: 'text-terracotta bg-terracotta/10' },
    { icon: ClipboardList, label: 'Examinations', value: stats.examinations, to: '/examinations', color: 'text-sage bg-sage/10' },
    { icon: BarChart3, label: 'Reports', value: stats.reports, to: '/reports', color: 'text-lavender bg-lavender/10' },
  ]

  const statusColor = {
    CREATED: 'badge-neutral',
    IN_PROGRESS: 'badge bg-olive/20 text-olive',
    COMPLETED: 'badge-strong',
    ABANDONED: 'badge-weak',
    ANALYZED: 'badge-strong',
    PROCESSING: 'badge bg-olive/20 text-olive',
    UPLOADED: 'badge-neutral',
    FAILED: 'badge-weak',
  }

  return (
    <div className="page-container animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="section-title">
          Good {getTimeOfDay()}, {user?.name?.split(' ')[0] || 'Student'}
        </h1>
        <p className="text-warmgray mt-1 text-sm">Your academic intelligence workspace.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {statCards.map(({ icon: Icon, label, value, to, color }) => (
          <Link key={to} to={to} className="card-hover group">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${color}`}>
              <Icon size={18} />
            </div>
            <p className="text-3xl font-display font-bold text-charcoal">{loading ? '—' : value}</p>
            <p className="text-warmgray text-sm mt-0.5">{label}</p>
            <div className="flex items-center gap-1 mt-3 text-xs font-medium text-warmgray group-hover:text-terracotta transition-colors">
              View all <ArrowRight size={12} />
            </div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Recent Documents */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-display font-semibold text-charcoal">Recent Documents</h2>
            <Link to="/documents" className="text-xs text-terracotta hover:underline font-medium">View all</Link>
          </div>
          {recentDocs.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="mx-auto mb-2 text-sand" size={32} />
              <p className="text-warmgray text-sm">No documents yet</p>
              <Link to="/documents" className="btn-primary mt-4 text-sm py-2 px-4 inline-flex">
                <Plus size={14} /> Upload PDF
              </Link>
            </div>
          ) : (
            <div className="space-y-2.5">
              {recentDocs.map((doc) => (
                <Link key={doc.id} to={`/documents/${doc.id}`} className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-ivory transition-colors group">
                  <div className="w-8 h-8 rounded-md bg-terracotta/10 flex items-center justify-center flex-shrink-0">
                    <FileText className="text-terracotta" size={15} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-charcoal truncate group-hover:text-terracotta transition-colors">
                      {doc.original_filename}
                    </p>
                    <p className="text-xs text-warmgray">{(doc.file_size / 1024).toFixed(0)} KB</p>
                  </div>
                  <span className={statusColor[doc.status] || 'badge-neutral'}>{doc.status}</span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recent Examinations */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-display font-semibold text-charcoal">Recent Examinations</h2>
            <Link to="/examinations" className="text-xs text-terracotta hover:underline font-medium">View all</Link>
          </div>
          {recentExams.length === 0 ? (
            <div className="text-center py-8">
              <ClipboardList className="mx-auto mb-2 text-sand" size={32} />
              <p className="text-warmgray text-sm">No examinations yet</p>
              <Link to="/examinations" className="btn-primary mt-4 text-sm py-2 px-4 inline-flex">
                <Plus size={14} /> Start Examination
              </Link>
            </div>
          ) : (
            <div className="space-y-2.5">
              {recentExams.map((exam) => (
                <div key={exam.id} className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-ivory transition-colors">
                  <div className="w-8 h-8 rounded-md bg-sage/10 flex items-center justify-center flex-shrink-0">
                    <ClipboardList className="text-sage" size={15} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-charcoal">Exam #{exam.id}</p>
                    <p className="text-xs text-warmgray">
                      {exam.questions_asked_count}/{exam.max_questions} questions
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={statusColor[exam.status] || 'badge-neutral'}>{exam.status}</span>
                    {exam.status === 'IN_PROGRESS' && (
                      <Link to={`/examinations/${exam.id}/session`} className="btn-primary text-xs py-1 px-2">
                        Resume
                      </Link>
                    )}
                    {exam.status === 'COMPLETED' && (
                      <Link to={`/reports/${exam.id}`} className="btn-secondary text-xs py-1 px-2">
                        Report
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Start Guide */}
      {stats.documents === 0 && !loading && (
        <div className="card border-terracotta/20 bg-terracotta/5">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-terracotta/20 flex items-center justify-center flex-shrink-0 mt-0.5">
              <TrendingUp className="text-terracotta" size={20} />
            </div>
            <div>
              <h2 className="text-base font-display font-semibold text-charcoal mb-2">Get started with ExamForge</h2>
              <ol className="list-decimal list-inside space-y-1.5 text-sm text-warmgray">
                <li>Upload a study PDF on the <Link to="/documents" className="text-terracotta hover:underline font-medium">Documents</Link> page.</li>
                <li>Wait for AI analysis to complete — typically 10–30 seconds.</li>
                <li>Create a new examination from <Link to="/examinations" className="text-terracotta hover:underline font-medium">Examinations</Link>.</li>
                <li>Answer each question thoughtfully — your report awaits.</li>
              </ol>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function getTimeOfDay() {
  const h = new Date().getHours()
  if (h < 12) return 'morning'
  if (h < 17) return 'afternoon'
  return 'evening'
}
