import { useEffect, useState, useCallback } from 'react'
import { Brain, TrendingUp, TrendingDown, Minus, AlertCircle, RefreshCw, BarChart2 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { knowledgeApi, docsApi } from '../services/api.js'
import toast from 'react-hot-toast'

const STATUS_CONFIG = {
  STRONG:               { label: 'Strong', color: '#788875', bg: 'bg-sage/15', icon: TrendingUp },
  PARTIALLY_UNDERSTOOD: { label: 'Partial', color: '#A4A17C', bg: 'bg-olive/15', icon: Minus },
  WEAK:                 { label: 'Weak', color: '#B8755D', bg: 'bg-terracotta/15', icon: TrendingDown },
  NOT_ASSESSED:         { label: 'Not Assessed', color: '#A99AAF', bg: 'bg-lavender/15', icon: AlertCircle },
}

export default function KnowledgePage() {
  const [profiles, setProfiles] = useState([])
  const [docs, setDocs] = useState({})
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const { data } = await knowledgeApi.profiles()
      setProfiles(data)
      // Load doc names
      if (data.length > 0) {
        const docIds = [...new Set(data.map((p) => p.document_id))]
        const docMap = {}
        await Promise.all(
          docIds.map(async (id) => {
            try {
              const r = await docsApi.get(id)
              docMap[id] = r.data.original_filename
            } catch { docMap[id] = `Document ${id}` }
          })
        )
        setDocs(docMap)
      }
    } catch {
      toast.error('Failed to load knowledge profiles')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  if (loading) return (
    <div className="page-container">
      <div className="card animate-pulse py-12 text-center text-warmgray">Loading knowledge profiles…</div>
    </div>
  )

  return (
    <div className="page-container animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="section-title">Knowledge Profile</h1>
          <p className="text-warmgray text-sm mt-0.5">Your cumulative knowledge assessment across all documents</p>
        </div>
        <button onClick={load} className="btn-ghost text-sm">
          <RefreshCw size={15} />
        </button>
      </div>

      {profiles.length === 0 ? (
        <div className="card text-center py-16">
          <Brain className="mx-auto mb-3 text-sand" size={40} />
          <p className="font-medium text-charcoal">No knowledge profiles yet</p>
          <p className="text-warmgray text-sm mt-1">Complete an examination to build your knowledge profile.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {profiles.map((profile) => {
            const scorePct = Math.round((profile.overall_score || 0) * 100)
            const docName = docs[profile.document_id] || `Document ${profile.document_id}`

            const categoryData = [
              { name: 'Strong', count: profile.strong_topics?.length || 0, color: '#788875' },
              { name: 'Partial', count: profile.partial_topics?.length || 0, color: '#A4A17C' },
              { name: 'Weak', count: profile.weak_topics?.length || 0, color: '#B8755D' },
              { name: 'Not Assessed', count: profile.not_assessed_topics?.length || 0, color: '#A99AAF' },
            ]

            return (
              <div key={profile.id} className="card">
                {/* Header */}
                <div className="flex items-start justify-between gap-4 mb-5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-terracotta/15 flex items-center justify-center flex-shrink-0">
                      <Brain className="text-terracotta" size={20} />
                    </div>
                    <div>
                      <p className="font-medium text-charcoal">{docName}</p>
                      <p className="text-xs text-warmgray">
                        {profile.total_examinations} examination{profile.total_examinations !== 1 ? 's' : ''} taken
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-display font-bold text-charcoal">{scorePct}%</p>
                    <p className="text-xs text-warmgray">Overall</p>
                  </div>
                </div>

                {/* Score bar */}
                <div className="mb-5">
                  <div className="flex justify-between text-xs text-warmgray mb-1">
                    <span>Knowledge Score</span>
                    <span>{scorePct}%</span>
                  </div>
                  <div className="bg-sand rounded-full h-2">
                    <div
                      className="h-2 rounded-full bg-terracotta transition-all duration-700"
                      style={{ width: `${scorePct}%` }}
                    />
                  </div>
                </div>

                {/* Category breakdown */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                  {categoryData.map(({ name, count, color }) => (
                    <div key={name} className="bg-ivory rounded-lg p-3 text-center">
                      <p className="text-xl font-bold font-display" style={{ color }}>{count}</p>
                      <p className="text-xs text-warmgray mt-0.5">{name}</p>
                    </div>
                  ))}
                </div>

                {/* Mini bar chart */}
                {categoryData.some((c) => c.count > 0) && (
                  <ResponsiveContainer width="100%" height={80}>
                    <BarChart data={categoryData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                      <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#827B72' }} tickLine={false} />
                      <YAxis tick={false} axisLine={false} />
                      <Tooltip
                        contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #E9DFD1' }}
                        formatter={(v, n) => [v, 'Topics']}
                      />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {categoryData.map((entry, idx) => (
                          <Cell key={idx} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
