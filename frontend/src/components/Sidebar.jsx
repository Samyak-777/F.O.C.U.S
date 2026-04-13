export default function Sidebar({ activeTab, setActiveTab, onLogout, user }) {
  const navItems = [
    { id: 'session', icon: '🎯', label: 'Session Control' },
    { id: 'attendance', icon: '📋', label: 'Attendance' },
    { id: 'heatmap', icon: '🗺️', label: 'Engagement Map' },
    { id: 'alerts', icon: '📱', label: 'Phone Alerts' },
    { id: 'export', icon: '📤', label: 'Export Reports' },
  ]

  return (
    <div className="sidebar">
      <div style={{ marginBottom: '24px', padding: '0 8px' }}>
        <h2 className="gradient-text" style={{ fontSize: '22px', fontWeight: 800 }}>FOCUS</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '11px', marginTop: '2px' }}>
          AI Classroom Assistant
        </p>
      </div>

      <nav style={{ flex: 1 }}>
        {navItems.map(item => (
          <div
            key={item.id}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </div>
        ))}
      </nav>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
        <div style={{ padding: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
          {user?.email || 'Faculty'}
        </div>
        <div className="nav-item" onClick={onLogout} style={{ color: 'var(--accent-rose)' }}>
          <span>🚪</span>
          <span>Sign Out</span>
        </div>
      </div>
    </div>
  )
}
