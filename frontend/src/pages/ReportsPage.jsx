import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart3, RefreshCw, ExternalLink, FileDown } from 'lucide-react'
import toast from 'react-hot-toast'
import { reportsApi } from '../services/api.js'

export default function ReportsPage() {
  const navigate = useNavigate()
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchReports = useCallback(async () => {
    try {
      const { data } = await reportsApi.list()
      setReports(data)
    } catch {
      toast.error('Failed to load reports')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchReports() }, [fetchReports])

  const scoreLabel = (s) => {
    if (!s) return 'N/A'
    const pct = Math.round(s * 100)
    if (pct >= 85) return { label: 'Excellent', color: 'text-sage' }
    if (pct >= 70) return { label: 'Good', color: 'text-sage' }
    if (pct >= 55) return { label: 'Satisfactory', color: 'text-olive' }
    if (pct >= 40) return { label: 'Needs Work', color: 'text-terracotta' }
    return { label: 'Poor', color: 'text-terracotta' }
  }

  return (
    <div className="page-container animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="section-title">Reports</h1>
          <p className="text-warmgray text-sm mt-0.5">
            {loading ? 'Loading…' : `${reports.length} report${reports.length !== 1 ? 's' : ''}`}
          </p>
        </div>
        <button onClick={fetchReports} className="btn-ghost text-sm">
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="card animate-pulse py-6 flex gap-4">
              <div className="w-12 h-12 rounded-lg bg-sand" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-sand rounded w-1/3" />
                <div className="h-3 bg-sand rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : reports.length === 0 ? (
        <div className="card text-center py-16">
          <BarChart3 className="mx-auto mb-3 text-sand" size={40} />
          <p className="font-medium text-charcoal">No reports yet</p>
          <p className="text-warmgray text-sm mt-1">Complete an examination to generate your first knowledge assessment report.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => {
            const pct = report.overall_score ? Math.round(report.overall_score * 100) : 0
            const { label: scoreText, color: scoreColor } = scoreLabel(report.overall_score) || {}
            return (
              <div
                key={report.id}
                className="card cursor-pointer hover:shadow-card hover:-translate-y-0.5 transition-all duration-200"
                onClick={() => navigate(`/reports/${report.examination_id}`)}
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-lavender/15 flex items-center justify-center flex-shrink-0">
                    <span className="text-lavender font-display font-bold text-lg">{pct}%</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-charcoal">Exam #{report.examination_id} Report</p>
                      <span className={`text-xs font-medium ${scoreColor}`}>{scoreText}</span>
                      {report.provider_mode && (
                        <span className="badge-neutral text-xs">{report.provider_mode.toUpperCase()}</span>
                      )}
                    </div>
                    <p className="text-xs text-warmgray mt-0.5">
                      Generated {new Date(report.generated_at).toLocaleDateString()}
                      {report.strong_concepts?.length > 0 && ` · ${report.strong_concepts.length} strong topic(s)`}
                      {report.weak_concepts?.length > 0 && ` · ${report.weak_concepts.length} weak topic(s)`}
                    </p>
                    {/* Mini bars */}
                    <div className="mt-2 flex items-center gap-2">
                      <div className="bg-sand rounded-full h-1.5 flex-1 max-w-[200px]">
                        <div className="bg-sage h-1.5 rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={async (e) => {
                        e.stopPropagation()
                        try {
                          await reportsApi.downloadPdf(report.examination_id)
                          toast.success('PDF report downloaded')
                        } catch {
                          toast.error('Failed to download PDF')
                        }
                      }}
                      className="p-1.5 rounded-md text-warmgray hover:text-terracotta hover:bg-terracotta/10 transition-colors"
                      title="Download PDF"
                    >
                      <FileDown size={15} />
                    </button>
                    <ExternalLink size={14} className="text-warmgray/40" />
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
