import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import useSessionSocket from '../hooks/useSessionSocket'

export default function AttendancePanel({ sessionId }) {
  const [records, setRecords] = useState([])
  const [overrideRoll, setOverrideRoll] = useState('')
  const [overrideStatus, setOverrideStatus] = useState('Present')
  const [overrideComment, setOverrideComment] = useState('')
  const { authFetch } = useAuth()

  // Load initial records
  useEffect(() => {
    if (!sessionId) return
    authFetch(`/api/attendance/session/${sessionId}`)
      .then(r => r.json())
      .then(setRecords)
      .catch(err => console.error('Failed to load initial attendance:', err))
  }, [sessionId, authFetch])

  // Real-time update handler
  const handleAttendanceMessage = useCallback((data) => {
    // data.attendance is a dict: { roll: { status, confidence, failure_code } }
    const formatted = Object.entries(data.attendance).map(([roll, details]) => ({
      roll_number: roll,
      status: details.status,
      ai_confidence: details.confidence,
      failure_code: details.failure_code,
      marked_at: new Date().toISOString()
    }))
    setRecords(formatted)
  }, [])

  useSessionSocket(sessionId, {
    attendance: handleAttendanceMessage
  })

  const handleOverride = async () => {
    if (!overrideComment || overrideComment.trim().length < 5) {
      alert('Comment is mandatory and must be at least 5 characters')
      return
    }
    try {
      const res = await authFetch('/api/attendance/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          roll_number: overrideRoll,
          session_id: String(sessionId),
          new_status: overrideStatus,
          comment: overrideComment
        })
      })
      const data = await res.json()
      if (res.ok) {
        alert(`Override successful: ${data.record.roll_number} → ${data.record.new_status}`)
        setOverrideRoll('')
        setOverrideComment('')
      } else {
        alert(data.detail || 'Override failed')
      }
    } catch { alert('Network error') }
  }

  const StatusBadge = ({ status }) => {
    const cls = status === 'Present' ? 'badge-present' :
                status === 'Late' ? 'badge-late' :
                status === 'Absent' ? 'badge-absent' : 'badge-unverified'
    return <span className={`badge ${cls}`}>{status}</span>
  }

  if (!sessionId) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '48px' }}>
        <p style={{ color: 'var(--text-muted)', fontSize: '16px' }}>
          Start a session first to view attendance data
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="glass-card" style={{ marginBottom: '16px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>
          ✏️ Manual Override
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '12px' }}>
          Override preserves original AI record in immutable audit log (ATT-06)
        </p>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ minWidth: '140px' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: 'var(--text-muted)' }}>
              Roll Number
            </label>
            <input
              id="override-roll"
              value={overrideRoll}
              onChange={e => setOverrideRoll(e.target.value)}
              placeholder="BT23CSE001"
              style={{ width: '140px' }}
            />
          </div>
          <div style={{ minWidth: '120px' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: 'var(--text-muted)' }}>
              New Status
            </label>
            <select
              id="override-status"
              value={overrideStatus}
              onChange={e => setOverrideStatus(e.target.value)}
              style={{ width: '120px' }}
            >
              <option value="Present">Present</option>
              <option value="Late">Late</option>
              <option value="Absent">Absent</option>
            </select>
          </div>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: 'var(--text-muted)' }}>
              Comment (required, min 5 chars)
            </label>
            <input
              id="override-comment"
              value={overrideComment}
              onChange={e => setOverrideComment(e.target.value)}
              placeholder="Reason for override..."
            />
          </div>
          <button
            id="override-submit"
            className="btn btn-primary"
            onClick={handleOverride}
            disabled={!overrideRoll || overrideComment.trim().length < 5}
          >
            Override
          </button>
        </div>
      </div>

      <div className="glass-card">
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>
          📊 Session #{sessionId} Attendance
        </h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Roll No.</th>
              <th>Status</th>
              <th>AI Confidence</th>
              <th>Time</th>
              <th>Overridden</th>
            </tr>
          </thead>
          <tbody>
            {records.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '32px' }}>
                  Attendance data will appear here in real-time during scan
                </td>
              </tr>
            ) : records.map((r, i) => (
              <tr key={i}>
                <td>{r.roll_number}</td>
                <td><StatusBadge status={r.status} /></td>
                <td>{r.ai_confidence ? `${(r.ai_confidence*100).toFixed(1)}%` : '—'}</td>
                <td>{r.marked_at ? new Date(r.marked_at).toLocaleTimeString() : '—'}</td>
                <td>{r.is_overridden ? '✅' : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
