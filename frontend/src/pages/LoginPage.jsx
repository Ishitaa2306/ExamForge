import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BookOpen, Eye, EyeOff, ArrowRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { authApi } from '../services/api.js'
import { useAuthStore } from '../store/authStore.js'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    if (!email.trim() || !password) {
      toast.error('Please enter both email and password.')
      return
    }

    setLoading(true)
    try {
      const { data } = await authApi.login(email.trim(), password)
      useAuthStore.getState().setAuth(data.access_token, null)
      const { data: userData } = await authApi.me()
      setAuth(data.access_token, userData)
      toast.success('Signed in successfully.')
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid email or password. Please verify your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-cream flex flex-col justify-between px-4 py-8">
      {/* Top Header */}
      <div className="max-w-md mx-auto w-full flex items-center justify-between mb-4">
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 bg-terracotta rounded-lg flex items-center justify-center shadow-soft group-hover:scale-105 transition-transform">
            <BookOpen className="w-4 h-4 text-white" />
          </div>
          <span className="font-display text-xl font-bold text-charcoal">ExamForge</span>
        </Link>
        <Link to="/" className="text-xs font-semibold text-warmgray hover:text-charcoal transition-colors">
          Back to Overview
        </Link>
      </div>

      {/* Main Card */}
      <div className="w-full max-w-md mx-auto">
        <div className="card bg-white border border-sand p-8 sm:p-10 shadow-card rounded-2xl">
          <div className="mb-6">
            <h1 className="text-3xl font-display font-bold text-charcoal tracking-tight">Academic Sign In</h1>
            <p className="text-sm text-warmgray mt-1.5">
              Access your examination records and autonomous sessions.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Institutional or Student Email</label>
              <input
                type="email"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@university.edu"
                className="input-field"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="label mb-0">Password</label>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-field pr-11"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-warmgray hover:text-charcoal p-1 rounded-md transition-colors"
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-3 py-3 rounded-xl font-semibold shadow-soft hover:shadow-card transition-all"
            >
              {loading ? 'Authenticating...' : 'Sign In to Examination'}
              {!loading && <ArrowRight className="w-4 h-4" />}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-sand text-center">
            <p className="text-xs text-warmgray">
              New to ExamForge?{' '}
              <Link to="/register" className="text-terracotta font-semibold hover:underline">
                Register an examination profile
              </Link>
            </p>
          </div>
        </div>
      </div>

      <div className="text-center text-xs text-warmgray">
        Powered by Google Gemini & IBM Granite · Real-AI Examination Infrastructure
      </div>
    </div>
  )
}
