import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore.js'
import {
  LayoutDashboard, FileText, ClipboardList,
  BarChart3, Brain, LogOut, BookOpen, Settings,
} from 'lucide-react'

const navItems = [
  { to: '/dashboard',    label: 'Dashboard',      icon: LayoutDashboard },
  { to: '/documents',    label: 'Documents',      icon: FileText },
  { to: '/examinations', label: 'Examinations',   icon: ClipboardList },
  { to: '/reports',      label: 'Reports',        icon: BarChart3 },
  { to: '/knowledge',    label: 'Knowledge',      icon: Brain },
  { to: '/settings',     label: 'Settings',       icon: Settings },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-cream overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 bg-ivory border-r border-sand flex flex-col">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-sand">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-terracotta rounded-lg flex items-center justify-center flex-shrink-0">
              <BookOpen className="w-4 h-4 text-white" />
            </div>
            <div>
              <span className="font-display text-lg font-semibold text-charcoal leading-none">ExamForge</span>
              <p className="text-xs text-warmgray leading-none mt-0.5">AI Examiner</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-5 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? 'bg-terracotta/10 text-terracotta'
                    : 'text-warmgray hover:bg-sand/60 hover:text-charcoal'
                }`
              }
            >
              <Icon size={17} className="flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="px-3 py-4 border-t border-sand">
          <div className="flex items-center gap-3 px-2 py-2 rounded-lg">
            <div className="w-8 h-8 rounded-full bg-terracotta/20 text-terracotta flex items-center justify-center text-sm font-semibold flex-shrink-0">
              {user?.name?.[0]?.toUpperCase() ?? 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-charcoal truncate">{user?.name ?? 'Student'}</p>
              <p className="text-xs text-warmgray truncate">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-md text-warmgray hover:text-terracotta hover:bg-terracotta/10 transition-colors"
              title="Log out"
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
