import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft,
  FileDown,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertCircle,
  CheckCircle,
  BarChart2,
  Sparkles,
  BookOpen,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from 'recharts'
import { reportsApi } from '../services/api.js'
import toast from 'react-hot-toast'

const SCORE_CONFIG = (pct) => {
  if (pct >= 85) return { label: 'Distinction', color: '#788875', bg: 'bg-sage/15' }
  if (pct >= 70) return { label: 'Commended', color: '#788875', bg: 'bg-sage/15' }
  if (pct >= 55) return { label: 'Satisfactory', color: '#A4A17C', bg: 'bg-olive/15' }
  if (pct >= 40) return { label: 'Needs Review', color: '#B8755D', bg: 'bg-terracotta/15' }
  return { label: 'Unsatisfactory', color: '#B8755D', bg: 'bg-terracotta/15' }
}

export default function ReportDetailPage() {
  const { examinationId } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [retrying, setRetrying] = useState(false)
  const [downloadingPdf, setDownloadingPdf] = useState(false)

  useEffect(() => {
    loadReport()
  }, [examinationId]) // eslint-disable-line

  async function loadReport() {
    setLoading(true)
    setError(null)
    try {
      const { data } = await reportsApi.get(examinationId)
      setReport(data)
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to load report'
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  async function retryReport() {
    setRetrying(true)
    await loadReport()
    setRetrying(false)
  }

  async function handleDownloadPdf() {
    setDownloadingPdf(true)
    try {
      await reportsApi.downloadPdf(examinationId, `examforge-report-${examinationId}.pdf`)
      toast.success('Report PDF downloaded successfully.')
    } catch (err) {
      toast.error('Failed to download report PDF.')
    } finally {
      setDownloadingPdf(false)
    }
  }

  if (loading) {
    return (
      <div className="page-container py-16 text-center">
        <div className="w-10 h-10 border-2 border-terracotta border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-sm font-semibold text-charcoal">Gemini Report Generation Agent is compiling evidence...</p>
        <p className="text-xs text-warmgray mt-1">Aggregating IBM Granite semantic answer evaluations.</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page-container max-w-2xl py-12">
        <Link to="/reports" className="btn-ghost mb-6 -ml-2 text-sm inline-flex items-center gap-1.5">
          <ArrowLeft size={15} /> All Reports
        </Link>
        <div className="card text-center py-12 bg-white border border-sand shadow-soft rounded-2xl">
          <AlertCircle className="mx-auto mb-3 text-terracotta" size={40} />
          <h2 className="font-display text-xl font-bold text-charcoal mb-2">Report Not Ready</h2>
          <p className="text-warmgray text-sm mb-6 max-w-md mx-auto">{error}</p>
          <div className="flex gap-3 justify-center">
            <button onClick={retryReport} disabled={retrying} className="btn-primary text-sm">
              {retrying ? 'Refreshing...' : 'Retry Report Generation'}
            </button>
            <Link to={`/examinations/${examinationId}/session`} className="btn-secondary text-sm">
              Resume Examination
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (!report) return null

  const scorePct = Math.round((report.overall_score || 0) * 100)
  const cfg = SCORE_CONFIG(scorePct)

  // Topic bar chart data
  const topicData = report.topic_scores
    ? Object.entries(report.topic_scores).map(([tid, info]) => ({
        name: (typeof info === 'object' ? info.name : `Topic ${tid}`)?.slice(0, 30) || `Topic ${tid}`,
        score: typeof info === 'object' ? Math.round((info.score || 0) * 100) : Math.round(Number(info) * 100),
        status: typeof info === 'object' ? info.status : 'ASSESSED',
      }))
    : []

  const topicBarColor = (status) => {
    if (status === 'STRONG') return '#788875'
    if (status === 'PARTIALLY_UNDERSTOOD') return '#A4A17C'
    if (status === 'WEAK') return '#B8755D'
    return '#A99AAF'
  }

  return (
    <div className="page-container max-w-4xl animate-fade-in py-8">
      {/* Navigation & Action Bar */}
      <div className="flex items-center justify-between mb-6">
        <Link to="/reports" className="btn-ghost text-sm -ml-2 inline-flex items-center gap-1.5">
          <ArrowLeft size={15} /> All Reports
        </Link>
        <button
          onClick={handleDownloadPdf}
          disabled={downloadingPdf}
          className="btn-secondary text-sm inline-flex items-center gap-2 shadow-soft hover:shadow-card"
        >
          <FileDown size={16} />
          {downloadingPdf ? 'Exporting PDF...' : 'Download Certified PDF'}
        </button>
      </div>

      {/* Header Banner */}
      <div className="card bg-white border border-sand p-6 sm:p-8 mb-6 shadow-soft rounded-2xl">
        <div className="flex flex-col sm:flex-row sm:items-center gap-6">
          <div className={`w-24 h-24 rounded-2xl ${cfg.bg} flex flex-col items-center justify-center flex-shrink-0 border border-sand/60 shadow-soft`}>
            <span className="text-3xl font-display font-bold" style={{ color: cfg.color }}>
              {scorePct}%
            </span>
            <span className="text-xs font-bold uppercase tracking-wider mt-0.5" style={{ color: cfg.color }}>
              {cfg.label}
            </span>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 text-xs font-semibold text-terracotta uppercase tracking-wider mb-1">
              <Sparkles size={14} />
              Google Gemini Synthesized Performance Report
            </div>
            <h1 className="text-3xl font-display font-bold text-charcoal tracking-tight">
              Examination #{report.examination_id} Academic Review
            </h1>
            <p className="text-xs text-warmgray mt-2">
              Generated: {new Date(report.generated_at).toLocaleDateString(undefined, { dateStyle: 'long' })} ·
              Inference Mode: <strong className="text-charcoal uppercase">Live Dual AI (Gemini + Granite)</strong>
            </p>
          </div>
        </div>
      </div>

      {/* Grid: Topic Chart & Knowledge Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Topic performance chart */}
        {topicData.length > 0 && (
          <div className="card bg-white border border-sand p-6 shadow-soft rounded-2xl">
            <h2 className="text-base font-display font-bold text-charcoal mb-4">Topic-by-Topic Performance</h2>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topicData} layout="vertical" margin={{ left: 0, right: 16 }}>
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: '#827B72' }} tickLine={false} />
                  <YAxis dataKey="name" type="category" width={140} tick={{ fontSize: 11, fill: '#302E2B' }} tickLine={false} />
                  <Tooltip
                    contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E9DFD1', backgroundColor: '#FCFAF6' }}
                    formatter={(v) => [`${v}%`, 'Strength']}
                  />
                  <Bar dataKey="score" radius={[0, 6, 6, 0]}>
                    {topicData.map((entry, idx) => (
                      <Cell key={idx} fill={topicBarColor(entry.status)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Knowledge Summary */}
        <div className="card bg-white border border-sand p-6 shadow-soft rounded-2xl">
          <h2 className="text-base font-display font-bold text-charcoal mb-4">Demonstrated Understanding</h2>
          <div className="space-y-3.5">
            {[
              { icon: CheckCircle, label: 'Strong Mastery Concepts', items: report.strong_concepts, color: 'text-sage', badge: 'bg-sage/15 text-sage' },
              { icon: TrendingUp, label: 'Partially Understood Areas', items: report.partial_concepts, color: 'text-olive', badge: 'bg-olive/15 text-olive' },
              { icon: TrendingDown, label: 'Critical Knowledge Gaps', items: report.weak_concepts, color: 'text-terracotta', badge: 'bg-terracotta/15 text-terracotta' },
              { icon: Minus, label: 'Not Assessed (Unprobed)', items: report.not_assessed_concepts, color: 'text-warmgray', badge: 'bg-sand text-warmgray' },
            ].map(({ icon: Icon, label, items, color, badge }) => (
              <div key={label} className="border-b border-sand/60 pb-3 last:border-0 last:pb-0">
                <div className="flex items-center gap-2 mb-1">
                  <Icon size={14} className={color} />
                  <span className="text-xs font-semibold text-charcoal">{label}</span>
                </div>
                <div className="flex flex-wrap gap-1.5 pl-5">
                  {!items || items.length === 0 ? (
                    <span className="text-xs text-warmgray italic">None recorded</span>
                  ) : (
                    items.map((item, i) => (
                      <span key={i} className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${badge}`}>
                        {typeof item === 'object' ? JSON.stringify(item) : item}
                      </span>
                    ))
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Revision Priorities & Recommendations */}
      {report.recommendations && report.recommendations.length > 0 && (
        <div className="card bg-white border border-sand p-6 sm:p-8 mb-6 shadow-soft rounded-2xl">
          <h2 className="text-lg font-display font-bold text-charcoal mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-terracotta" />
            Prioritized Revision Plan
          </h2>
          <div className="space-y-3">
            {report.recommendations.map((rec, i) => {
              const isObj = typeof rec === 'object' && rec !== null
              return (
                <div
                  key={i}
                  className="flex items-start gap-3.5 p-3.5 rounded-xl bg-ivory/60 border border-sand/60 text-xs"
                >
                  <span className="w-6 h-6 rounded-full bg-terracotta text-white font-bold flex items-center justify-center flex-shrink-0 mt-0.5 text-xs shadow-soft">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    {isObj ? (
                      <>
                        <div className="flex items-center gap-2 mb-1">
                          <strong className="text-charcoal font-semibold">{rec.topic || 'Recommended Focus'}</strong>
                          {rec.priority && (
                            <span className="badge bg-terracotta/20 text-terracotta text-[10px]">
                              {rec.priority}
                            </span>
                          )}
                        </div>
                        <p className="text-charcoal/90 mb-1">{rec.focus_area}</p>
                        {rec.concrete_action && (
                          <p className="text-warmgray italic">{rec.concrete_action}</p>
                        )}
                      </>
                    ) : (
                      <p className="text-charcoal text-sm leading-relaxed">{rec}</p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
