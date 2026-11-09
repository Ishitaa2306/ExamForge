import { useEffect, useState } from 'react'
import {
  Settings,
  User,
  Cpu,
  Database,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Sparkles,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore.js'
import { settingsApi } from '../services/api.js'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { user } = useAuthStore()
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [testing, setTesting] = useState(false)
  const [testResults, setTestResults] = useState(null)

  useEffect(() => {
    loadStatus()
  }, [])

  async function loadStatus() {
    setLoading(true)
    try {
      const { data } = await settingsApi.status()
      setStatus(data)
    } catch (err) {
      toast.error('Failed to retrieve system status.')
    } finally {
      setLoading(false)
    }
  }

  async function handleTestProviders() {
    setTesting(true)
    setTestResults(null)
    try {
      const { data } = await settingsApi.testProviders()
      setTestResults(data)
      if (data.gemini?.status === 'connected' && data.granite?.status === 'connected') {
        toast.success('Both AI providers successfully authenticated and verified.')
      } else {
        toast('Provider check completed. See results below.')
      }
    } catch (err) {
      toast.error('Provider connectivity test failed.')
    } finally {
      setTesting(false)
    }
  }

  const agentMapping = [
    { name: 'Document Understanding Agent', provider: 'Google Gemini', model: status?.gemini?.model_id || 'Configured in .env', role: 'Curriculum structure, formulas, definitions' },
    { name: 'Question Generation Agent', provider: 'Google Gemini', model: status?.gemini?.model_id || 'Configured in .env', role: '8-category question authoring with rubrics' },
    { name: 'Autonomous Examination Agent', provider: 'Google Gemini', model: status?.gemini?.model_id || 'Configured in .env', role: 'Adaptive examiner, follow-ups, difficulty tuning' },
    { name: 'Final Report Generation Agent', provider: 'Google Gemini', model: status?.gemini?.model_id || 'Configured in .env', role: 'Academic performance report synthesis' },
    { name: 'Answer Evaluation Agent', provider: 'IBM Granite (watsonx.ai)', model: status?.granite?.model_id || 'Configured in .env', role: '5-criterion semantic answer scoring' },
    { name: 'Knowledge Assessment Agent', provider: 'IBM Granite (watsonx.ai)', model: status?.granite?.model_id || 'Configured in .env', role: 'Topic mastery profiling & gap detection' },
  ]

  return (
    <div className="page-container max-w-3xl animate-fade-in py-8">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="section-title">System & AI Infrastructure Settings</h1>
          <p className="text-sm text-warmgray mt-1">
            Review your student identity, database status, and real AI provider connectivity.
          </p>
        </div>

        <button
          onClick={loadStatus}
          disabled={loading}
          className="btn-secondary text-xs inline-flex items-center gap-1.5 py-2 px-3 shadow-soft"
          title="Refresh status"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Account Profile Card */}
      <div className="card bg-white border border-sand p-6 shadow-soft rounded-2xl mb-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-xl bg-terracotta/15 text-terracotta flex items-center justify-center">
            <User size={18} />
          </div>
          <div>
            <h2 className="text-base font-display font-bold text-charcoal">Student Profile</h2>
            <p className="text-xs text-warmgray">Your registered examinee profile.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label text-xs">Examinee Name</label>
            <p className="input-field bg-ivory/60 cursor-default text-charcoal font-medium text-sm">
              {user?.name || 'Academic Student'}
            </p>
          </div>
          <div>
            <label className="label text-xs">Registered Email</label>
            <p className="input-field bg-ivory/60 cursor-default text-charcoal font-medium text-sm">
              {user?.email || 'student@university.edu'}
            </p>
          </div>
        </div>
      </div>

      {/* AI Providers & Live Model Connectivity */}
      <div className="card bg-white border border-sand p-6 sm:p-8 shadow-soft rounded-2xl mb-6">
        <div className="flex items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-sage/20 text-sage flex items-center justify-center">
              <Cpu size={18} />
            </div>
            <div>
              <h2 className="text-base font-display font-bold text-charcoal">Live AI Model Providers</h2>
              <p className="text-xs text-warmgray">
                Real inference infrastructure. Private keys remain secure on the backend server.
              </p>
            </div>
          </div>

          <button
            onClick={handleTestProviders}
            disabled={testing}
            className="btn-primary text-xs py-2 px-3.5 shadow-soft hover:shadow-card inline-flex items-center gap-1.5"
          >
            {testing ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Pinging Providers...</span>
              </>
            ) : (
              <>
                <Sparkles size={14} />
                <span>Verify Live AI Connections</span>
              </>
            )}
          </button>
        </div>

        {/* Provider Status Tiles */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          {/* Gemini Tile */}
          <div className="p-4 rounded-xl bg-ivory/60 border border-sand">
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-sm text-charcoal">Google Gemini</span>
              {status?.gemini?.configured ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-sage">
                  <CheckCircle2 size={13} /> Configured
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-terracotta">
                  <XCircle size={13} /> Unconfigured
                </span>
              )}
            </div>
            <p className="text-xs text-warmgray">
              Active Model: <strong className="text-charcoal font-mono">{status?.gemini?.model_id || 'Configured in .env'}</strong>
            </p>
            {testResults?.gemini && (
              <div className="mt-2 pt-2 border-t border-sand text-xs">
                {testResults.gemini.status === 'connected' ? (
                  <span className="text-sage font-medium">✓ Real Gemini inference verified</span>
                ) : (
                  <span className="text-terracotta">✗ {testResults.gemini.message}</span>
                )}
              </div>
            )}
          </div>

          {/* Granite Tile */}
          <div className="p-4 rounded-xl bg-ivory/60 border border-sand">
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-sm text-charcoal">IBM watsonx.ai Granite</span>
              {status?.granite?.configured ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-sage">
                  <CheckCircle2 size={13} /> Configured
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-terracotta">
                  <XCircle size={13} /> Unconfigured
                </span>
              )}
            </div>
            <p className="text-xs text-warmgray">
              Active Model: <strong className="text-charcoal font-mono">{status?.granite?.model_id || 'Configured in .env'}</strong>
            </p>
            {testResults?.granite && (
              <div className="mt-2 pt-2 border-t border-sand text-xs">
                {testResults.granite.status === 'connected' ? (
                  <span className="text-sage font-medium">✓ Real Granite inference verified</span>
                ) : (
                  <span className="text-terracotta">✗ {testResults.granite.message}</span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Database Status */}
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-ivory/40 border border-sand/80 text-xs text-charcoal">
          <div className="flex items-center gap-2.5">
            <Database size={15} className="text-sage" />
            <span>Relational Store: <strong>{status?.database?.engine || 'PostgreSQL'}</strong></span>
          </div>
          {status?.database?.connected ? (
            <span className="text-sage font-semibold flex items-center gap-1">
              <CheckCircle2 size={13} /> Connected
            </span>
          ) : (
            <span className="text-terracotta font-semibold flex items-center gap-1">
              <XCircle size={13} /> Disconnected
            </span>
          )}
        </div>
      </div>

      {/* Six-Agent Responsibility Mapping Card */}
      <div className="card bg-white border border-sand p-6 sm:p-8 shadow-soft rounded-2xl">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-xl bg-lavender/20 text-lavender flex items-center justify-center">
            <Settings size={18} />
          </div>
          <div>
            <h2 className="text-base font-display font-bold text-charcoal">Six-Agent Responsibility Mapping</h2>
            <p className="text-xs text-warmgray">Strict architectural model allocation.</p>
          </div>
        </div>

        <div className="space-y-3">
          {agentMapping.map((agent) => (
            <div
              key={agent.name}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-xl bg-ivory/40 border border-sand/60 text-xs"
            >
              <div>
                <strong className="text-charcoal block">{agent.name}</strong>
                <span className="text-warmgray">{agent.role}</span>
              </div>
              <div className="sm:text-right flex-shrink-0">
                <span className="badge bg-terracotta/15 text-terracotta font-semibold">
                  {agent.provider}
                </span>
                <span className="block text-[11px] text-warmgray font-mono mt-0.5">
                  {agent.model}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
