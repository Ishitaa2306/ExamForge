import { useEffect, useState, useCallback } from 'react'
import { Brain, TrendingUp, TrendingDown, Minus, AlertCircle, RefreshCw, BarChart2 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { knowledgeApi, docsApi } from '../services/api.js'
import toast from 'react-hot-toast'

export default function KnowledgePage() {
  const [profiles, setProfiles] = useState([])
  const [docs, setDocs] = useState({})
  const [topicNames, setTopicNames] = useState({})
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const { data } = await knowledgeApi.profiles()
      setProfiles(data)
      // Load document and topic metadata
      if (data.length > 0) {
        const docIds = [...new Set(data.map((p) => p.document_id))]
        const docMap = {}
        const topicMap = {}
        await Promise.all(
          docIds.map(async (id) => {
            try {
              const [rDoc, rMap] = await Promise.all([
                docsApi.get(id),
                docsApi.knowledgeMap(id).catch(() => ({ data: { topics: [] } })),
              ])
              docMap[id] = rDoc.data.original_filename
              if (rMap.data?.topics) {
                rMap.data.topics.forEach((t) => {
                  topicMap[t.id] = t.name
                })
              }
            } catch {
              docMap[id] = `Document ${id}`
            }
          })
        )
        setDocs(docMap)
        setTopicNames(topicMap)
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
          <p className="text-warmgray text-sm mt-0.5">Your cumulative knowledge assessment synthesized by IBM Granite</p>
        </div>
        <button onClick={load} className="btn-ghost text-sm" title="Refresh">
          <RefreshCw size={15} />
        </button>
      </div>

      {profiles.length === 0 ? (
        <div className="card text-center py-16">
          <Brain className="mx-auto mb-3 text-sand" size={40} />
          <p className="font-medium text-charcoal">No knowledge profiles yet</p>
          <p className="text-warmgray text-sm mt-1">Complete an examination to build your cumulative knowledge profile.</p>
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
                    <p className="text-xs text-warmgray">Demonstrated Mastery</p>
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

                {/* Category breakdown stat cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                  {categoryData.map(({ name, count, color }) => (
                    <div key={name} className="bg-ivory rounded-lg p-3 text-center border border-sand/40">
                      <p className="text-xl font-bold font-display" style={{ color }}>{count}</p>
                      <p className="text-xs text-warmgray mt-0.5">{name}</p>
                    </div>
                  ))}
                </div>

                {/* Mini bar chart */}
                {categoryData.some((c) => c.count > 0) && (
                  <div className="mb-5">
                    <ResponsiveContainer width="100%" height={90}>
                      <BarChart data={categoryData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                        <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#827B72' }} tickLine={false} />
                        <YAxis tick={false} axisLine={false} />
                        <Tooltip
                          contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #E9DFD1', backgroundColor: '#FCFAF6' }}
                          formatter={(v) => [v, 'Topics']}
                        />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                          {categoryData.map((entry, idx) => (
                            <Cell key={idx} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Detailed Topic Categorization Lists */}
                <div className="pt-4 border-t border-sand grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  {profile.strong_topics?.length > 0 && (
                    <div className="bg-sage/10 rounded-lg p-3 border border-sage/20">
                      <p className="font-semibold text-sage mb-2 flex items-center gap-1.5">
                        <TrendingUp size={14} /> Strong Topics ({profile.strong_topics.length})
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {profile.strong_topics.map((tid) => (
                          <span key={tid} className="bg-white/90 px-2 py-0.5 rounded text-charcoal border border-sage/30 shadow-xs">
                            {topicNames[tid] || (typeof tid === 'string' ? tid : `Topic #${tid}`)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {profile.partial_topics?.length > 0 && (
                    <div className="bg-olive/10 rounded-lg p-3 border border-olive/20">
                      <p className="font-semibold text-olive mb-2 flex items-center gap-1.5">
                        <Minus size={14} /> Partially Understood ({profile.partial_topics.length})
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {profile.partial_topics.map((tid) => (
                          <span key={tid} className="bg-white/90 px-2 py-0.5 rounded text-charcoal border border-olive/30 shadow-xs">
                            {topicNames[tid] || (typeof tid === 'string' ? tid : `Topic #${tid}`)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {profile.weak_topics?.length > 0 && (
                    <div className="bg-terracotta/10 rounded-lg p-3 border border-terracotta/20">
                      <p className="font-semibold text-terracotta mb-2 flex items-center gap-1.5">
                        <TrendingDown size={14} /> Areas for Improvement ({profile.weak_topics.length})
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {profile.weak_topics.map((tid) => (
                          <span key={tid} className="bg-white/90 px-2 py-0.5 rounded text-charcoal border border-terracotta/30 shadow-xs">
                            {topicNames[tid] || (typeof tid === 'string' ? tid : `Topic #${tid}`)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {profile.not_assessed_topics?.length > 0 && (
                    <div className="bg-lavender/10 rounded-lg p-3 border border-lavender/20">
                      <p className="font-semibold text-lavender mb-2 flex items-center gap-1.5">
                        <AlertCircle size={14} /> Not Yet Assessed ({profile.not_assessed_topics.length})
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {profile.not_assessed_topics.map((tid) => (
                          <span key={tid} className="bg-white/90 px-2 py-0.5 rounded text-charcoal border border-lavender/30 shadow-xs">
                            {topicNames[tid] || (typeof tid === 'string' ? tid : `Topic #${tid}`)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
