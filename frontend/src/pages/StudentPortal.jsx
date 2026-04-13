import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import EnrollmentPage from './EnrollmentPage'

export default function StudentPortal() {
  const [attendance, setAttendance] = useState([])
  const [consentStatus, setConsentStatus] = useState(null)
  const [activeTab, setActiveTab] = useState('attendance')
  const { authFetch, logout, user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    authFetch('/api/students/me/attendance')
      .then(r => r.json())
      .then(setAttendance)
      .catch(() => {})
  }, [])

  const handleLogout = () => { logout(); navigate('/login') }

  const StatusBadge = ({ status }) => {
    const cls = status === 'Present' ? 'badge-present' :
                status === 'Late' ? 'badge-late' :
                status === 'Absent' ? 'badge-absent' : 'badge-unverified'
    return <span className={`badge ${cls}`}>{status}</span>
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-dark)' }}>
      <header style={{
        background: 'var(--bg-card)',
        borderBottom: '1px solid var(--border)',
        padding: '16px 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h1 className="gradient-text" style={{ fontSize: '20px', fontWeight: 700 }}>FOCUS</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Student Portal</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>{user?.email}</span>
          <button className="btn btn-outline" onClick={handleLogout}>Sign Out</button>
        </div>
      </header>

      <div style={{ maxWidth: '900px', margin: '32px auto', padding: '0 20px' }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
          {['attendance', 'enrollment', 'consent'].map(tab => (
            <button
              key={tab}
              className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'attendance' ? '📋 My Attendance' : tab === 'enrollment' ? '📸 Face Enrollment' : '🔒 Privacy & Consent'}
            </button>
          ))}
        </div>

        {activeTab === 'attendance' ? (
          <div className="glass-card animate-in">
            <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>Attendance History</h2>
            {attendance.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No attendance records yet.</p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Session</th>
                    <th>Status</th>
                    <th>AI Confidence</th>
                    <th>Date</th>
                    <th>Overridden</th>
                  </tr>
                </thead>
                <tbody>
                  {attendance.map((r, i) => (
                    <tr key={i}>
                      <td>#{r.session_id}</td>
                      <td><StatusBadge status={r.status} /></td>
                      <td>{r.ai_confidence ? `${(r.ai_confidence*100).toFixed(1)}%` : '—'}</td>
                      <td>{r.marked_at ? new Date(r.marked_at).toLocaleDateString() : '—'}</td>
                      <td>{r.is_overridden ? '✅ Yes' : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        ) : activeTab === 'enrollment' ? (
          <div className="animate-in">
            <EnrollmentPage />
          </div>
        ) : (
          <div className="glass-card animate-in">
            <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>🔒 Privacy & Consent</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: '1.6' }}>
              Under the Digital Personal Data Protection Act (2023), you have the right to give
              or revoke biometric consent at any time. Your facial embedding will be permanently
              deleted within 24 hours of revocation.
            </p>

            {consentStatus && (
              <div style={{
                padding: '12px 16px', borderRadius: '8px', marginBottom: '16px',
                background: consentStatus.type === 'success' ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
                border: `1px solid ${consentStatus.type === 'success' ? '#22c55e' : '#ef4444'}`,
                color: consentStatus.type === 'success' ? '#22c55e' : '#ef4444',
                fontSize: '14px'
              }}>
                {consentStatus.message}
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                id="give-consent-btn"
                className="btn btn-success"
                onClick={async () => {
                  try {
                    const res = await authFetch('/api/students/me/consent/give', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ language: 'en' })
                    })
                    const data = await res.json()
                    if (res.ok) {
                      setConsentStatus({ type: 'success', message: `✅ Consent given! Status: ${data.status}` })
                    } else {
                      setConsentStatus({ type: 'error', message: `❌ ${data.detail || 'Failed to give consent'}` })
                    }
                  } catch (err) {
                    setConsentStatus({ type: 'error', message: '❌ Network error. Please try again.' })
                  }
                }}
              >
                Give Consent
              </button>
              <button
                id="revoke-consent-btn"
                className="btn btn-danger"
                onClick={async () => {
                  if (window.confirm('Are you sure? Your biometric data will be permanently deleted.')) {
                    try {
                      const res = await authFetch('/api/students/me/consent/revoke', { method: 'POST' })
                      const data = await res.json()
                      if (res.ok) {
                        setConsentStatus({ type: 'success', message: '✅ Consent revoked. Your biometric data has been deleted.' })
                      } else {
                        setConsentStatus({ type: 'error', message: `❌ ${data.detail || 'Failed to revoke consent'}` })
                      }
                    } catch (err) {
                      setConsentStatus({ type: 'error', message: '❌ Network error. Please try again.' })
                    }
                  }
                }}
              >
                Revoke Consent
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
