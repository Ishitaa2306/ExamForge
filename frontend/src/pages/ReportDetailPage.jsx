import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, FileDown, TrendingUp, TrendingDown, Minus, AlertCircle, CheckCircle, BarChart2 } from 'lucide-react'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'
import { reportsApi } from '../services/api.js'
import toast from 'react-hot-toast'

const SCORE_CONFIG = (pct) => {
  if (pct >= 85) return { label: 'Excellent', color: '#788875', bg: 'bg-sage/15' }
  if (pct >= 70) return { label: 'Good', color: '#788875', bg: 'bg-sage/15' }
  if (pct >= 55) return { label: 'Satisfactory', color: '#A4A17C', bg: 'bg-olive/15' }
  if (pct >= 40) return { label: 'Needs Work', color: '#B8755D', bg: 'bg-terracotta/15' }
  return { label: 'Poor', color: '#B8755D', bg: 'bg-terracotta/15' }
}

export default function ReportDetailPage() {
  const { examinationId } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [retrying, setRetrying] = useState(false)

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

  if (loading) return (
    <div className="page-container">
      <div className="card animate-pulse py-16 text-center text-warmgray">Loading report…</div>
    </div>
  )

  if (error) return (
    <div className="page-container">
      <Link to="/reports" className="btn-ghost mb-6 -ml-2 text-sm">
        <ArrowLeft size={15} /> Back to reports
      </Link>
      <div className="card text-center py-12">
        <AlertCircle className="mx-auto mb-3 text-terracotta" size={36} />
        <h2 className="font-display font-semibold text-charcoal mb-2">Report not available</h2>
        <p className="text-warmgray text-sm mb-5">{error}</p>
        <div className="flex gap-3 justify-center">
          <button onClick={retryReport} disabled={retrying} className="btn-primary">
            {retrying ? 'Checking…' : 'Retry'}
          </button>
          <Link to={`/examinations/${examinationId}/session`} className="btn-secondary">Resume Exam</Link>
        </div>
      </div>
    </div>
  )

  if (!report) return null

  const scorePct = Math.round((report.overall_score || 0) * 100)
  const cfg = SCORE_CONFIG(scorePct)

  // Topic bar chart data
  const topicData = report.topic_scores
    ? Object.entries(report.topic_scores).map(([tid, info]) => ({
        name: (typeof info === 'object' ? info.name : `T${tid}`)?.slice(0, 25) || `T${tid}`,
        score: typeof info === 'object' ? Math.round(info.score * 100) : Math.round(info * 100),
        status: typeof info === 'object' ? info.status : '—',
      }))
    : []

  const topicBarColor = (status) => {
    if (status === 'STRONG') return '#788875'
    if (status === 'PARTIALLY_UNDERSTOOD') return '#A4A17C'
    if (status === 'WEAK') return '#B8755D'
    return '#A99AAF'
  }

  return (
    <div className="page-container max-w-4xl animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <Link to="/reports" className="btn-ghost text-sm -ml-2">
          <ArrowLeft size={15} /> All Reports
        </Link>
        <a
          href={reportsApi.pdfUrl(examinationId)}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary text-sm"
        >
          <FileDown size={15} /> Download PDF
        </a>
      </div>

      {/* Header */}
      <div className="card mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          <div className={`w-20 h-20 rounded-2xl ${cfg.bg} flex flex-col items-center justify-center flex-shrink-0`}>
            <span className="text-3xl font-display font-bold" style={{ color: cfg.color }}>{scorePct}%</span>
            <span className="text-xs font-medium" style={{ color: cfg.color }}>{cfg.label}</span>
          </div>
          <div>
            <h1 className="section-title">Examination #{report.examination_id} Report</h1>
            <p className="text-sm text-warmgray mt-1">
              Generated {new Date(report.generated_at).toLocaleDateString()} ·
              Mode: <span className="font-medium text-charcoal">{(report.provider_mode || 'mock').toUpperCase()}</span>
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        {/* Topic performance chart */}
        {topicData.length > 0 && (
          <div className="card">
            <h2 className="text-sm font-semibold text-charcoal mb-4">Topic Performance</h2>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={topicData} layout="vertical" margin={{ left: 0, right: 16 }}>
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: '#827B72' }} tickLine={false} />
                <YAxis dataKey="name" type="category" width={140} tick={{ fontSize: 10, fill: '#827B72' }} tickLine={false} />
                <Tooltip
                  contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #E9DFD1' }}
                  formatter={(v) => [`${v}%`, 'Score']}
                />
                <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                  {topicData.map((entry, idx) => (
                    <Cell key={idx} fill={topicBarColor(entry.status)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Summary */}
        <div className="card">
          <h2 className="text-sm font-semibold text-charcoal mb-4">Knowledge Summary</h2>
          <div className="space-y-2.5">
            {[
              { icon: CheckCircle, label: 'Strong Concepts', items: report.strong_concepts, color: 'text-sage' },
              { icon: TrendingUp, label: 'Partially Understood', items: report.partial_concepts, color: 'text-olive' },
              { icon: TrendingDown, label: 'Needs Improvement', items: report.weak_concepts, color: 'text-terracotta' },
              { icon: Minus, label: 'Not Assessed', items: report.not_assessed_concepts, color: 'text-warmgray' },
            ].map(({ icon: Icon, label, items, color }) => (
              <div key={label} className="flex items-start gap-2.5">
                <Icon size={15} className={`${color} mt-0.5 flex-shrink-0`} />
                <div>
                  <p className="text-xs font-medium text-charcoal">{label}</p>
                  <p className="text-xs text-warmgray mt-0.5">
                    {!items || items.length === 0 ? 'None' : items.join(', ')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {report.recommendations?.length > 0 && (
        <div className="card mb-5">
          <h2 className="text-sm font-semibold text-charcoal mb-4">Revision Priorities</h2>
          <ol className="space-y-2">
            {report.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-warmgray">
                <span className="w-5 h-5 rounded-full bg-terracotta/15 text-terracotta text-xs font-semibold flex items-center justify-center flex-shrink-0 mt-0.5">{i + 1}</span>
                {rec}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Topic table */}
      {topicData.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-semibold text-charcoal mb-4">Detailed Topic Scores</h2>
          <div className="space-y-2">
            {topicData.map((t) => (
              <div key={t.name} className="flex items-center gap-3">
                <p className="text-sm text-charcoal w-40 flex-shrink-0 truncate">{t.name}</p>
                <div className="flex-1 bg-sand rounded-full h-2">
                  <div
                    className="h-2 rounded-full transition-all duration-500"
                    style={{ width: `${t.score}%`, backgroundColor: topicBarColor(t.status) }}
                  />
                </div>
                <span className="text-xs text-warmgray w-10 text-right">{t.score}%</span>
                <span className="text-xs w-24 text-warmgray truncate">{t.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
