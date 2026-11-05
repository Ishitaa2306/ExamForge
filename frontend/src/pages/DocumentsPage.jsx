import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Trash2, RefreshCw, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'
import { docsApi } from '../services/api.js'

const STATUS_BADGE = {
  UPLOADED:   'badge-neutral',
  PROCESSING: 'badge bg-olive/20 text-olive animate-pulse-soft',
  ANALYZED:   'badge-strong',
  FAILED:     'badge-weak',
}

export default function DocumentsPage() {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState([])
  const [total, setTotal] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(true)
  const documentsRef = useRef(documents)
  documentsRef.current = documents

  const fetchDocuments = useCallback(async () => {
    try {
      const { data } = await docsApi.list()
      setDocuments(data.documents)
      setTotal(data.total)
    } catch {
      toast.error('Failed to load documents')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDocuments()
    // Auto-refresh periodically if any document is being processed
    const iv = setInterval(() => {
      if (documentsRef.current.some((d) => d.status === 'PROCESSING')) {
        fetchDocuments()
      }
    }, 3500)
    return () => clearInterval(iv)
  }, [fetchDocuments])

  const onDrop = useCallback(async (accepted) => {
    if (!accepted.length) return
    setUploading(true)
    try {
      await docsApi.upload(accepted[0])
      toast.success('Document uploaded — AI analysis started')
      fetchDocuments()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [fetchDocuments])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: uploading,
  })

  async function deleteDocument(id, e) {
    e.stopPropagation()
    if (!confirm('Delete this document and all associated examinations?')) return
    try {
      await docsApi.delete(id)
      toast.success('Document deleted')
      fetchDocuments()
    } catch {
      toast.error('Failed to delete document')
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  return (
    <div className="page-container animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="section-title">Documents</h1>
          <p className="text-warmgray text-sm mt-0.5">
            {loading ? 'Loading…' : `${total} document${total !== 1 ? 's' : ''}`}
          </p>
        </div>
        <button onClick={fetchDocuments} className="btn-ghost text-sm">
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200 mb-6 ${
          isDragActive
            ? 'border-terracotta bg-terracotta/5 scale-[1.01]'
            : 'border-sand hover:border-terracotta/40 hover:bg-ivory/80'
        } ${uploading ? 'opacity-60 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto mb-3 text-warmgray" size={28} />
        <p className="text-charcoal font-medium">
          {uploading ? 'Uploading…' : isDragActive ? 'Drop your PDF here' : 'Drag & drop a PDF, or click to browse'}
        </p>
        <p className="text-warmgray text-sm mt-1">PDF only · Max 50 MB</p>
      </div>

      {/* List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse py-5 flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-sand" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-sand rounded w-1/2" />
                <div className="h-3 bg-sand rounded w-1/4" />
              </div>
            </div>
          ))}
        </div>
      ) : documents.length === 0 ? (
        <div className="card text-center py-16">
          <FileText className="mx-auto mb-3 text-sand" size={40} />
          <p className="font-medium text-charcoal">No documents yet</p>
          <p className="text-warmgray text-sm mt-1">Upload your first PDF study material above to get started.</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="card flex items-center gap-4 cursor-pointer hover:shadow-card hover:-translate-y-0.5 transition-all duration-200"
              onClick={() => navigate(`/documents/${doc.id}`)}
            >
              <div className="w-10 h-10 rounded-lg bg-terracotta/10 flex items-center justify-center flex-shrink-0">
                <FileText className="text-terracotta" size={18} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-charcoal truncate">{doc.original_filename}</p>
                <p className="text-xs text-warmgray mt-0.5">
                  {formatSize(doc.file_size)}
                  {doc.page_count ? ` · ${doc.page_count} pages` : ''}
                  {doc.word_count ? ` · ${doc.word_count?.toLocaleString()} words` : ''}
                </p>
              </div>
              <span className={STATUS_BADGE[doc.status] || 'badge-neutral'}>{doc.status}</span>
              {doc.status === 'FAILED' && (
                <button
                  onClick={async (e) => {
                    e.stopPropagation()
                    try {
                      await docsApi.analyze(doc.id)
                      toast.success('Analysis restarted!')
                      fetchDocuments()
                    } catch (err) {
                      toast.error('Failed to restart analysis')
                    }
                  }}
                  className="px-2.5 py-1 rounded-lg text-xs font-semibold text-terracotta bg-terracotta/10 hover:bg-terracotta/20 transition-colors flex items-center gap-1.5 shadow-2xs"
                  title="Retry Analysis"
                >
                  <RefreshCw size={13} /> Retry
                </button>
              )}
              <button
                onClick={(e) => deleteDocument(doc.id, e)}
                className="p-1.5 rounded-md text-warmgray hover:text-terracotta hover:bg-terracotta/10 transition-colors"
                title="Delete"
              >
                <Trash2 size={15} />
              </button>
              <ExternalLink size={14} className="text-warmgray/50 flex-shrink-0" />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
