import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore.js'
import Layout from './components/layout/Layout.jsx'
import LandingPage from './pages/LandingPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import DocumentsPage from './pages/DocumentsPage.jsx'
import DocumentDetailPage from './pages/DocumentDetailPage.jsx'
import QuestionBankPage from './pages/QuestionBankPage.jsx'
import ExaminationsPage from './pages/ExaminationsPage.jsx'
import ExamSessionPage from './pages/ExamSessionPage.jsx'
import ReportsPage from './pages/ReportsPage.jsx'
import ReportDetailPage from './pages/ReportDetailPage.jsx'
import KnowledgePage from './pages/KnowledgePage.jsx'
import SettingsPage from './pages/SettingsPage.jsx'

function PrivateRoute({ children }) {
  const token = useAuthStore((s) => s.token)
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  const token = useAuthStore((s) => s.token)

  return (
    <Routes>
      {/* Public Landing & Authentication */}
      <Route path="/" element={token ? <Navigate to="/dashboard" replace /> : <LandingPage />} />
      <Route path="/landing" element={<LandingPage />} />
      <Route path="/login" element={token ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
      <Route path="/register" element={token ? <Navigate to="/dashboard" replace /> : <RegisterPage />} />

      {/* Authenticated Application Shell */}
      <Route
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/documents/:id" element={<DocumentDetailPage />} />
        <Route path="/documents/:id/questions" element={<QuestionBankPage />} />
        <Route path="/questions" element={<QuestionBankPage />} />
        <Route path="/examinations" element={<ExaminationsPage />} />
        <Route path="/examinations/:id/session" element={<ExamSessionPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/reports/:examinationId" element={<ReportDetailPage />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
