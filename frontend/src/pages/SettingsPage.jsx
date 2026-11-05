import { useState } from 'react'
import { Settings, User, Key, Eye, EyeOff, CheckCircle } from 'lucide-react'
import { useAuthStore } from '../store/authStore.js'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { user } = useAuthStore()
  const [showKey, setShowKey] = useState(false)

  // In mock mode, display configuration info
  const providerMode = 'MOCK'

  return (
    <div className="page-container max-w-2xl animate-fade-in">
      <h1 className="section-title mb-8">Settings</h1>

      {/* Account */}
      <div className="card mb-5">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-lg bg-terracotta/15 flex items-center justify-center">
            <User className="text-terracotta" size={17} />
          </div>
          <h2 className="text-base font-display font-semibold text-charcoal">Account</h2>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Name</label>
            <p className="input-field bg-ivory cursor-not-allowed text-warmgray">{user?.name}</p>
          </div>
          <div>
            <label className="label">Email</label>
            <p className="input-field bg-ivory cursor-not-allowed text-warmgray">{user?.email}</p>
          </div>
        </div>
        <p className="text-xs text-warmgray mt-3">Account management is not yet available in this version.</p>
      </div>

      {/* AI Provider */}
      <div className="card mb-5">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-lg bg-sage/15 flex items-center justify-center">
            <Key className="text-sage" size={17} />
          </div>
          <h2 className="text-base font-display font-semibold text-charcoal">AI Provider Configuration</h2>
        </div>

        <div className="flex items-center gap-3 mb-5 p-3 bg-olive/10 rounded-lg">
          <CheckCircle className="text-olive flex-shrink-0" size={16} />
          <div>
            <p className="text-sm font-medium text-charcoal">Running in MOCK mode</p>
            <p className="text-xs text-warmgray">All AI inferences use deterministic mock responses. No API keys required.</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-sm font-semibold text-charcoal mb-2">Google Gemini (Document Analysis, Questions, Examination, Reports)</p>
            <div className="flex items-center gap-2">
              <input
                type={showKey ? 'text' : 'password'}
                value="••••••••••••••••••••••"
                readOnly
                className="input-field bg-ivory cursor-not-allowed flex-1"
              />
              <button onClick={() => setShowKey(!showKey)} className="btn-ghost p-2.5">
                {showKey ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
            <p className="text-xs text-warmgray mt-1">Set GEMINI_API_KEY in your .env file to enable live mode.</p>
          </div>

          <div>
            <p className="text-sm font-semibold text-charcoal mb-2">IBM Granite via watsonx.ai (Answer Evaluation, Knowledge Assessment)</p>
            <input
              type="password"
              value="••••••••••••••••••••••"
              readOnly
              className="input-field bg-ivory cursor-not-allowed"
            />
            <p className="text-xs text-warmgray mt-1">Set WATSONX_API_KEY and WATSONX_PROJECT_ID in your .env file.</p>
          </div>

          <div className="p-4 bg-ivory rounded-lg">
            <p className="text-xs font-semibold text-charcoal mb-2">To enable LIVE mode:</p>
            <ol className="text-xs text-warmgray space-y-1 list-decimal list-inside">
              <li>Add your API keys to the <code className="bg-sand px-1 rounded">.env</code> file in the project root.</li>
              <li>Set <code className="bg-sand px-1 rounded">AI_PROVIDER_MODE=live</code>.</li>
              <li>Restart the backend server: <code className="bg-sand px-1 rounded">uvicorn app.main:app --reload</code>.</li>
            </ol>
          </div>
        </div>
      </div>

      {/* Provider mapping */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-lg bg-lavender/15 flex items-center justify-center">
            <Settings className="text-lavender" size={17} />
          </div>
          <h2 className="text-base font-display font-semibold text-charcoal">Agent → Provider Mapping</h2>
        </div>
        <div className="space-y-2">
          {[
            { agent: 'Document Understanding', provider: 'Gemini' },
            { agent: 'Question Generation', provider: 'Gemini' },
            { agent: 'Examination Agent', provider: 'Gemini' },
            { agent: 'Answer Evaluation', provider: 'Granite (IBM)' },
            { agent: 'Knowledge Assessment', provider: 'Granite (IBM)' },
            { agent: 'Report Generation', provider: 'Gemini' },
          ].map(({ agent, provider }) => (
            <div key={agent} className="flex items-center justify-between py-2 border-b border-sand last:border-0">
              <span className="text-sm text-charcoal">{agent}</span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded ${provider.includes('IBM') ? 'bg-sage/15 text-sage' : 'bg-terracotta/15 text-terracotta'}`}>
                {provider}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
