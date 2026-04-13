import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import AttendancePanel from '../components/AttendancePanel'
import HeatmapPanel from '../components/HeatmapPanel'
import PhoneAlertPanel from '../components/PhoneAlertPanel'
import SessionControl from '../components/SessionControl'
import ExportPanel from '../components/ExportPanel'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('session')
  const [sessionId, setSessionId] = useState(null)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const tabs = {
    session: <SessionControl sessionId={sessionId} setSessionId={setSessionId} />,
    attendance: <AttendancePanel sessionId={sessionId} />,
    heatmap: <HeatmapPanel sessionId={sessionId} />,
    alerts: <PhoneAlertPanel sessionId={sessionId} />,
    export: <ExportPanel />,
  }

  return (
    <div className="layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} onLogout={handleLogout} user={user} />
      <div className="main-content">
        <div style={{ marginBottom: '24px' }}>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>
            {activeTab === 'session' ? '🎯 Session Control' :
             activeTab === 'attendance' ? '📋 Attendance' :
             activeTab === 'heatmap' ? '🗺️ Engagement Heatmap' :
             activeTab === 'alerts' ? '📱 Phone Alerts' :
             '📤 Export Reports'}
          </h1>
          {sessionId && (
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
              Active Session: #{sessionId}
            </p>
          )}
        </div>
        <div className="animate-in">
          {tabs[activeTab]}
        </div>
      </div>
    </div>
  )
}
