import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import useSessionSocket from '../hooks/useSessionSocket'

export default function HeatmapPanel({ sessionId }) {
  const [heatmap, setHeatmap] = useState(null)
  const [loading, setLoading] = useState(false)
  const { authFetch } = useAuth()

  useEffect(() => {
    if (!sessionId) return
    setLoading(true)
    authFetch(`/api/engagement/heatmap/${sessionId}`)
      .then(r => r.json())
      .then(data => { setHeatmap(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [sessionId, authFetch])

  // Real-time update handler
  const handleCompleteMessage = useCallback((data) => {
    setHeatmap(data.heatmap)
  }, [])

  useSessionSocket(sessionId, {
    session_complete: handleCompleteMessage
  })

  if (!sessionId) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '48px' }}>
        <p style={{ color: 'var(--text-muted)' }}>Start a session to view engagement heatmap</p>
      </div>
    )
  }

  const getZoneClass = (zone) => {
    if (!zone || zone.insufficient_data) return 'heatmap-insufficient'
    if (zone.state === 'Active') return 'heatmap-active'
    if (zone.state === 'Passive') return 'heatmap-passive'
    return 'heatmap-disengaged'
  }

  const zones = heatmap?.zones || {}
  const rows = 4, cols = 3

  return (
    <div>
      <div className="glass-card" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Classroom Engagement Map</h3>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Faculty-only view • Min 8 students/zone
          </span>
        </div>

        <div className="heatmap-grid" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
          {Array.from({ length: rows * cols }).map((_, i) => {
            const r = Math.floor(i / cols) + 1
            const c = (i % cols) + 1
            const zoneId = `R${r}C${c}`
            const zone = zones[zoneId]

            return (
              <div key={zoneId} className={`heatmap-cell ${getZoneClass(zone)}`}>
                <div style={{ fontSize: '11px', opacity: 0.7 }}>{zoneId}</div>
                {zone ? (
                  <>
                    <div style={{ fontSize: '16px', fontWeight: 700 }}>{zone.state}</div>
                    <div style={{ fontSize: '11px' }}>
                      {zone.student_count || 0} students
                    </div>
                    {zone.active_pct !== undefined && (
                      <div style={{ fontSize: '10px', opacity: 0.8 }}>
                        A:{zone.active_pct}% P:{zone.passive_pct}% D:{zone.disengaged_pct}%
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ fontSize: '13px' }}>No data</div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      <div className="glass-card">
        <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Legend</h4>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', fontSize: '13px' }}>
          <span>🟢 Active (focused)</span>
          <span>🟡 Passive (partly distracted)</span>
          <span>🔴 Disengaged</span>
          <span>⬜ Insufficient Data (&lt;8 students)</span>
        </div>
      </div>
    </div>
  )
}
