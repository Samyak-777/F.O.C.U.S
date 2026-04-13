import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function SessionControl({ sessionId, setSessionId }) {
  const [batchId, setBatchId] = useState('')
  const [roomId, setRoomId] = useState('')
  const [loading, setLoading] = useState(false)
  const { authFetch } = useAuth()

  const startSession = async () => {
    setLoading(true)
    try {
      const res = await authFetch('/api/sessions/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          batch_id: batchId,
          scheduled_start: new Date().toISOString(),
          room_id: roomId
        })
      })
      const data = await res.json()
      setSessionId(data.session_id)
    } catch (e) {
      alert('Failed to start session')
    }
    setLoading(false)
  }

  const stopSession = async () => {
    if (!sessionId) return
    try {
      await authFetch(`/api/sessions/${sessionId}/stop`, { method: 'POST' })
      setSessionId(null)
    } catch { alert('Failed to stop session') }
  }

  return (
    <div>
      <div className="stats-grid" style={{ marginBottom: '24px' }}>
        <div className="stat-card">
          <span className="stat-label">Status</span>
          <span className="stat-value" style={{ color: sessionId ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>
            {sessionId ? 'LIVE' : 'IDLE'}
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Session ID</span>
          <span className="stat-value" style={{ fontSize: '24px' }}>
            {sessionId ? `#${sessionId}` : '—'}
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Scan Window</span>
          <span className="stat-value" style={{ fontSize: '24px' }}>7 min</span>
        </div>
      </div>

      {!sessionId ? (
        <div className="glass-card">
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Start New Session</h3>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '200px' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                Batch ID
              </label>
              <input
                id="batch-id-input"
                value={batchId}
                onChange={e => setBatchId(e.target.value)}
                placeholder="e.g. CSE-B-S6"
              />
            </div>
            <div style={{ flex: 1, minWidth: '200px' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                Room ID
              </label>
              <input
                id="room-id-input"
                value={roomId}
                onChange={e => setRoomId(e.target.value)}
                placeholder="e.g. LH-201"
              />
            </div>
          </div>
          <button
            id="start-session-btn"
            className="btn btn-success"
            onClick={startSession}
            disabled={loading || !batchId}
            style={{ marginTop: '16px' }}
          >
            {loading ? '⏳ Starting...' : '▶️ Start Attendance Scan'}
          </button>
        </div>
      ) : (
        <div className="glass-card">
          <div style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            marginBottom: '16px'
          }}>
            <div style={{
              width: '12px', height: '12px', borderRadius: '50%',
              background: 'var(--accent-emerald)'
            }} className="pulse" />
            <span style={{ fontWeight: 600 }}>Session Active — Camera scanning...</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
            Face recognition is running. Students are being identified automatically.
            Navigate to the Attendance tab to view real-time results.
          </p>
          <button
            id="stop-session-btn"
            className="btn btn-danger"
            onClick={stopSession}
          >
            ⏹️ End Session & Generate Heatmap
          </button>
        </div>
      )}
    </div>
  )
}
