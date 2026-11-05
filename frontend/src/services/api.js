import axios from 'axios'
import { useAuthStore } from '../store/authStore.js'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Attach Bearer token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (name, email, password) =>
    api.post('/auth/register', { name, email, password }),

  login: (email, password) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },

  me: () => api.get('/auth/me'),
}

// ── Documents ─────────────────────────────────────────────────────────────────
export const docsApi = {
  list: (skip = 0, limit = 20) => api.get('/documents/', { params: { skip, limit } }),
  get: (id) => api.get(`/documents/${id}`),
  status: (id) => api.get(`/documents/${id}/status`),
  upload: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  analyze: (id) => api.post(`/documents/${id}/analyze`),
  knowledgeMap: (id) => api.get(`/documents/${id}/knowledge-map`),
  questions: (id, params = {}) => api.get(`/documents/${id}/questions`, { params }),
  delete: (id) => api.delete(`/documents/${id}`),
}

// ── Examinations ──────────────────────────────────────────────────────────────
export const examApi = {
  list: (skip = 0, limit = 20) => api.get('/examinations/', { params: { skip, limit } }),
  get: (id) => api.get(`/examinations/${id}`),
  create: (documentId, maxQuestions = 20) =>
    api.post('/examinations/', { document_id: documentId, max_questions: maxQuestions }),
  start: (id) => api.post(`/examinations/${id}/start`),
  answer: (examinationId, questionAskedId, answerText, timeTaken = null) =>
    api.post(`/examinations/${examinationId}/answer`, {
      question_asked_id: questionAskedId,
      answer_text: answerText,
      time_taken_seconds: timeTaken,
    }),
  progress: (id) => api.get(`/examinations/${id}/progress`),
  complete: (id) => api.post(`/examinations/${id}/complete`),
  abandon: (id) => api.post(`/examinations/${id}/abandon`),
}

// ── Reports ───────────────────────────────────────────────────────────────────
export const reportsApi = {
  list: (skip = 0, limit = 20) => api.get('/reports/', { params: { skip, limit } }),
  get: (examinationId) => api.get(`/reports/examination/${examinationId}`),
  pdfUrl: (examinationId) => `/api/reports/examination/${examinationId}/pdf`,
}

// ── Knowledge ─────────────────────────────────────────────────────────────────
export const knowledgeApi = {
  profile: (documentId) => api.get(`/knowledge/profile/${documentId}`),
  profiles: () => api.get('/knowledge/profiles'),
}

export default api
