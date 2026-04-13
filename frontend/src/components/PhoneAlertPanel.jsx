import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import useSessionSocket from '../hooks/useSessionSocket'

export default function PhoneAlertPanel({ sessionId }) {
  const [alerts, setAlerts] = useState([])
  const { authFetch } = useAuth()

  useEffect(() => {
    if (!sessionId) return
    authFetch(`/api/alerts/${sessionId}`)
      .then(r => r.json())
      .then(setAlerts)
      .catch(() => {})
  }, [sessionId, authFetch])

  // Real-time update handler
  const handleAlertMessage = useCallback((data) => {
    setAlerts(prev => [{
      id: Date.now(),
      zone_id: data.zone,
      confidence: data.confidence,
      detected_at: new Date().toISOString(),
      acknowledged: false
    }, ...prev])
  }, [])

  useSessionSocket(sessionId, {
    phone_alert: handleAlertMessage
  })

  if (!sessionId) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '48px' }}>
        <p style={{ color: 'var(--text-muted)' }}>Start a session to monitor phone alerts</p>
      </div>
    )
  }

  return (
    <div>
      {alerts.filter(a => !a.acknowledged).length > 0 && (
        <div className="alert-banner" style={{ marginBottom: '16px' }}>
          <div className="alert-icon" />
          <span style={{ color: 'var(--accent-rose)', fontWeight: 600 }}>
            {alerts.filter(a => !a.acknowledged).length} Active Phone Alert(s)
          </span>
        </div>
      )}

      <div className="glass-card">
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>
          📱 Phone Detection Log
        </h3>
        {alerts.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '32px' }}>
            No phone detections for this session
          </p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Zone</th>
                <th>Confidence</th>
                <th>Time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{a.zone_id || 'Unknown'}</td>
                  <td>{(a.confidence * 100).toFixed(1)}%</td>
                  <td>{a.detected_at ? new Date(a.detected_at).toLocaleTimeString() : '—'}</td>
                  <td>
                    <span className={`badge ${a.acknowledged ? 'badge-present' : 'badge-absent'}`}>
                      {a.acknowledged ? 'Acknowledged' : 'Active'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
