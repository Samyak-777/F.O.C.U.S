import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function ExportPanel() {
  const [batchId, setBatchId] = useState('')
  const [format, setFormat] = useState('pdf')
  const [exporting, setExporting] = useState(false)
  const { authFetch } = useAuth()

  const handleExport = async () => {
    if (!batchId) return
    setExporting(true)
    try {
      const res = await authFetch(`/api/admin/export/${batchId}?format=${format}`)
      if (!res.ok) {
        const err = await res.json()
        alert(err.detail || 'Export failed')
        setExporting(false)
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `attendance_${batchId}.${format === 'pdf' ? 'pdf' : 'xlsx'}`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert('Export failed')
    }
    setExporting(false)
  }

  return (
    <div className="glass-card">
      <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>📤 Export Attendance Report</h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
        SHA-256 signed • Max 200 students • Every export is audit-logged
      </p>
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            Batch ID
          </label>
          <input
            id="export-batch-id"
            value={batchId}
            onChange={e => setBatchId(e.target.value)}
            placeholder="e.g. CSE-B-S6"
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            Format
          </label>
          <select id="export-format" value={format} onChange={e => setFormat(e.target.value)}
                  style={{ width: '120px' }}>
            <option value="pdf">PDF</option>
            <option value="excel">Excel</option>
          </select>
        </div>
        <button
          id="export-btn"
          className="btn btn-primary"
          onClick={handleExport}
          disabled={exporting || !batchId}
        >
          {exporting ? '⏳ Generating...' : '⬇️ Download'}
        </button>
      </div>
    </div>
  )
}
