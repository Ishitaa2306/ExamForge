import { useEffect, useState, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  FileText,
  ClipboardList,
  BarChart3,
  ArrowRight,
  Plus,
  Play,
  Compass,
  Brain,
  Sparkles,
  Clock,
  Layers,
} from 'lucide-react'
import { docsApi, examApi, reportsApi, knowledgeApi } from '../services/api.js'
import { useAuthStore } from '../store/authStore.js'

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [stats, setStats] = useState({ documents: 0, examinations: 0, reports: 0 })
  const [recentDocs, setRecentDocs] = useState([])
  const [recentExams, setRecentExams] = useState([])
  const [activeExam, setActiveExam] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const [docs, exams, reports] = await Promise.all([
        docsApi.list(0, 5),
        examApi.list(0, 10),
        reportsApi.list(0, 5),
      ])
      const totalDocs = docs.data?.total || docs.data?.documents?.length || 0
      const totalExams = exams.data?.total || exams.data?.examinations?.length || 0
      const totalReports = Array.isArray(reports.data)
        ? reports.data.length
        : (reports.data?.total || reports.data?.reports?.length || 0)

      setStats({
        documents: totalDocs,
        examinations: totalExams,
        reports: totalReports,
      })
      setRecentDocs(docs.data.documents || [])
      const examList = exams.data.examinations || []
      setRecentExams(examList)

      // Find any active in-progress examination to resume
      const inProgress = examList.find((e) => e.status === 'IN_PROGRESS')
      setActiveExam(inProgress || null)
    } catch {
      // Handled silently
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const statusColor = {
    CREATED: 'badge-neutral',
    IN_PROGRESS: 'badge bg-olive/20 text-olive font-semibold',
    COMPLETED: 'badge-strong',
    ABANDONED: 'badge-weak',
    ANALYZED: 'badge-strong',
    PROCESSING: 'badge bg-olive/20 text-olive animate-pulse-soft',
    UPLOADED: 'badge-neutral',
    FAILED: 'badge-weak',
  }

  return (
    <div className="page-container animate-fade-in py-8">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-terracotta mb-1">
            <Sparkles size={14} />
            Academic Examination Dashboard
          </div>
          <h1 className="text-3xl font-display font-bold text-charcoal tracking-tight">
            Welcome, {user?.name || 'Student'}
          </h1>
          <p className="text-sm text-warmgray mt-1">
            Autonomous multi-agent academic testing workspace powered by Google Gemini and IBM Granite.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/documents"
            className="btn-secondary text-sm inline-flex items-center gap-2 shadow-soft hover:shadow-card"
          >
            <Plus size={15} />
            Upload PDF
          </Link>
          <Link
            to="/examinations"
            className="btn-primary text-sm inline-flex items-center gap-2 shadow-soft hover:shadow-card"
          >
            <Play size={15} />
            Start Examination
          </Link>
        </div>
      </div>

      {/* In-Progress Resume Alert Banner */}
      {activeExam && (
        <div className="card bg-terracotta/10 border-terracotta/30 p-5 rounded-2xl mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-soft animate-slide-up">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-terracotta text-white flex items-center justify-center flex-shrink-0 shadow-soft">
              <Clock size={20} className="animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-charcoal">Active Examination in Progress</span>
                <span className="badge bg-terracotta/20 text-terracotta font-semibold text-[11px]">
                  Turn {activeExam.questions_asked_count} of {activeExam.max_questions}
                </span>
              </div>
              <p className="text-xs text-warmgray mt-0.5">
                Your examination state has been persisted. Resume seamlessly right where you left off.
              </p>
            </div>
          </div>

          <Link
            to={`/examinations/${activeExam.id}/session`}
            className="btn-primary text-xs py-2 px-4 shadow-soft hover:shadow-card inline-flex items-center gap-1.5 self-start sm:self-center"
          >
            Resume Examination #{activeExam.id}
            <ArrowRight size={14} />
          </Link>
        </div>
      )}

      {/* Stats Counter Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
        <Link to="/documents" className="card bg-white p-5 rounded-xl border border-sand hover:shadow-card transition-all group">
          <div className="w-8 h-8 rounded-lg bg-terracotta/15 text-terracotta flex items-center justify-center mb-3">
            <FileText size={17} />
          </div>
          <p className="text-2xl font-display font-bold text-charcoal">{loading ? '—' : stats.documents}</p>
          <p className="text-xs text-warmgray mt-0.5">Curriculum Documents</p>
          <div className="flex items-center gap-1 mt-3 text-xs font-semibold text-terracotta group-hover:translate-x-0.5 transition-transform">
            View library <ArrowRight size={12} />
          </div>
        </Link>

        <Link to="/questions" className="card bg-white p-5 rounded-xl border border-sand hover:shadow-card transition-all group">
          <div className="w-8 h-8 rounded-lg bg-sage/20 text-sage flex items-center justify-center mb-3">
            <Compass size={17} />
          </div>
          <p className="text-2xl font-display font-bold text-charcoal">8 Categories</p>
          <p className="text-xs text-warmgray mt-0.5">Question Repository</p>
          <div className="flex items-center gap-1 mt-3 text-xs font-semibold text-sage group-hover:translate-x-0.5 transition-transform">
            Explore questions <ArrowRight size={12} />
          </div>
        </Link>

        <Link to="/examinations" className="card bg-white p-5 rounded-xl border border-sand hover:shadow-card transition-all group">
          <div className="w-8 h-8 rounded-lg bg-olive/20 text-olive flex items-center justify-center mb-3">
            <ClipboardList size={17} />
          </div>
          <p className="text-2xl font-display font-bold text-charcoal">{loading ? '—' : stats.examinations}</p>
          <p className="text-xs text-warmgray mt-0.5">Examinations Conducted</p>
          <div className="flex items-center gap-1 mt-3 text-xs font-semibold text-olive group-hover:translate-x-0.5 transition-transform">
            View history <ArrowRight size={12} />
          </div>
        </Link>

        <Link to="/reports" className="card bg-white p-5 rounded-xl border border-sand hover:shadow-card transition-all group">
          <div className="w-8 h-8 rounded-lg bg-lavender/25 text-lavender flex items-center justify-center mb-3">
            <BarChart3 size={17} />
          </div>
          <p className="text-2xl font-display font-bold text-charcoal">{loading ? '—' : stats.reports}</p>
          <p className="text-xs text-warmgray mt-0.5">Academic Reports</p>
          <div className="flex items-center gap-1 mt-3 text-xs font-semibold text-lavender group-hover:translate-x-0.5 transition-transform">
            View reports <ArrowRight size={12} />
          </div>
        </Link>
      </div>

      {/* Grid: Recent Documents & Examinations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Recent Documents */}
        <div className="card bg-white border border-sand p-6 rounded-2xl shadow-soft">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-sand">
            <h2 className="text-base font-display font-bold text-charcoal">Recent Study Material</h2>
            <Link to="/documents" className="text-xs text-terracotta hover:underline font-semibold">
              All documents
            </Link>
          </div>

          {recentDocs.length === 0 ? (
            <div className="text-center py-10">
              <FileText className="mx-auto mb-2 text-sand" size={36} />
              <p className="text-sm text-warmgray font-medium">No documents uploaded yet</p>
              <Link to="/documents" className="btn-primary mt-4 text-xs py-2 px-4 inline-flex">
                <Plus size={13} /> Upload Syllabus PDF
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recentDocs.slice(0, 4).map((doc) => (
                <Link
                  key={doc.id}
                  to={`/documents/${doc.id}`}
                  className="flex items-center justify-between gap-3 p-3 rounded-xl hover:bg-ivory/60 border border-transparent hover:border-sand/60 transition-all group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-terracotta/10 text-terracotta flex items-center justify-center flex-shrink-0">
                      <FileText size={16} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-charcoal truncate group-hover:text-terracotta transition-colors">
                        {doc.original_filename}
                      </p>
                      <p className="text-xs text-warmgray">
                        {doc.page_count ? `${doc.page_count} pages · ` : ''}
                        {(doc.file_size / 1024).toFixed(0)} KB
                      </p>
                    </div>
                  </div>
                  <span className={statusColor[doc.status] || 'badge-neutral'}>{doc.status}</span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recent Examinations */}
        <div className="card bg-white border border-sand p-6 rounded-2xl shadow-soft">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-sand">
            <h2 className="text-base font-display font-bold text-charcoal">Recent Examinations</h2>
            <Link to="/examinations" className="text-xs text-terracotta hover:underline font-semibold">
              All examinations
            </Link>
          </div>

          {recentExams.length === 0 ? (
            <div className="text-center py-10">
              <ClipboardList className="mx-auto mb-2 text-sand" size={36} />
              <p className="text-sm text-warmgray font-medium">No examinations conducted yet</p>
              <Link to="/examinations" className="btn-primary mt-4 text-xs py-2 px-4 inline-flex">
                <Play size={13} /> Start Examination
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recentExams.slice(0, 4).map((exam) => (
                <div
                  key={exam.id}
                  className="flex items-center justify-between gap-3 p-3 rounded-xl bg-ivory/40 border border-sand/60"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-sage/15 text-sage flex items-center justify-center flex-shrink-0">
                      <ClipboardList size={16} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-charcoal">Examination #{exam.id}</p>
                      <p className="text-xs text-warmgray">
                        {exam.questions_asked_count} of {exam.max_questions} questions · {exam.current_difficulty}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={statusColor[exam.status] || 'badge-neutral'}>{exam.status}</span>
                    {exam.status === 'IN_PROGRESS' && (
                      <Link
                        to={`/examinations/${exam.id}/session`}
                        className="btn-primary text-xs py-1 px-2.5"
                      >
                        Resume
                      </Link>
                    )}
                    {exam.status === 'COMPLETED' && (
                      <Link
                        to={`/reports/${exam.id}`}
                        className="btn-secondary text-xs py-1 px-2.5"
                      >
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
    </div>
  )
}
