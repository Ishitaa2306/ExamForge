import { useState } from 'react'
import { Outlet, NavLink, useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore.js'
import {
  LayoutDashboard,
  FileText,
  ClipboardList,
  BarChart3,
  Brain,
  LogOut,
  BookOpen,
  Settings,
  Compass,
  Menu,
  X,
} from 'lucide-react'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/documents', label: 'Documents & Upload', icon: FileText },
  { to: '/questions', label: 'Question Bank', icon: Compass },
  { to: '/examinations', label: 'Examinations', icon: ClipboardList },
  { to: '/knowledge', label: 'Knowledge Profile', icon: Brain },
  { to: '/reports', label: 'Academic Reports', icon: BarChart3 },
  { to: '/settings', label: 'Settings & Status', icon: Settings },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-cream overflow-hidden flex-col md:flex-row">
      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 bg-ivory border-b border-sand z-30 flex-shrink-0">
        <Link to="/dashboard" className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-terracotta rounded-lg flex items-center justify-center text-white shadow-soft">
            <BookOpen className="w-4 h-4" />
          </div>
          <span className="font-display text-lg font-bold text-charcoal">ExamForge</span>
        </Link>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 rounded-lg text-charcoal hover:bg-sand/60 transition-colors"
          aria-label="Toggle navigation menu"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </header>

      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          className="fixed inset-0 bg-charcoal/40 backdrop-blur-xs z-40 md:hidden"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed md:static inset-y-0 left-0 z-50
          w-64 flex-shrink-0 bg-ivory border-r border-sand flex flex-col justify-between shadow-soft
          transition-transform duration-200 ease-in-out
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        <div>
          {/* Logo Brand (Desktop) */}
          <div className="hidden md:flex items-center justify-between px-6 py-6 border-b border-sand">
            <Link to="/dashboard" className="flex items-center gap-3 group">
              <div className="w-9 h-9 bg-terracotta rounded-xl flex items-center justify-center flex-shrink-0 shadow-soft group-hover:scale-105 transition-transform">
                <BookOpen className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="font-display text-xl font-bold text-charcoal tracking-tight">ExamForge</span>
                <p className="text-[11px] font-medium text-warmgray uppercase tracking-wider mt-0.5">Autonomous Examiner</p>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="px-3 py-4 md:py-6 space-y-1 overflow-y-auto max-h-[calc(100vh-180px)]">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3.5 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-terracotta text-white shadow-soft font-semibold'
                      : 'text-charcoal/70 hover:bg-sand/60 hover:text-charcoal'
                  }`
                }
              >
                <Icon size={18} className="flex-shrink-0" />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        {/* User Info & Footer */}
        <div className="p-4 border-t border-sand bg-ivory/50">
          <div className="flex items-center justify-between gap-3 p-2 rounded-xl bg-white border border-sand/60 shadow-soft">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-terracotta/15 text-terracotta flex items-center justify-center text-xs font-bold flex-shrink-0">
                {user?.name?.[0]?.toUpperCase() ?? 'S'}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-charcoal truncate">{user?.name ?? 'Student'}</p>
                <p className="text-[10px] text-warmgray truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-warmgray hover:text-terracotta hover:bg-terracotta/10 transition-colors"
              title="Log out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto bg-cream">
        <Outlet />
      </main>
    </div>
  )
}
