/**
 * HeatmapGrid — Pure presentational component for zone-wise engagement heatmap.
 * US-03: Privacy-respecting, faculty-only view, min 8 students/zone.
 * Receives { data: { zones: { ... } } } as prop.
 */

const STATE_COLORS = {
  Active: '#22c55e',
  Passive: '#eab308',
  Disengaged: '#ef4444',
  Insufficient_Data: '#64748b'
};

export function HeatmapGrid({ data }) {
  const zones = data?.zones || {};
  const zoneIds = Object.keys(zones);

  return (
    <div>
      <div style={{ marginBottom: '8px', fontSize: '12px', color: '#94a3b8' }}>
        Faculty only view • Min 8 students/zone
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
        {zoneIds.length === 0 && (
          <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
            No zone data available
          </div>
        )}

        {zoneIds.map(zoneId => {
          const zone = zones[zoneId];
          const isInsufficient = zone.insufficient_data;
          const bgColor = isInsufficient
            ? '#334155'
            : (STATE_COLORS[zone.state] || '#334155');

          return (
            <div
              key={zoneId}
              title={isInsufficient ? 'Insufficient Data' : zone.state}
              style={{
                backgroundColor: bgColor,
                borderRadius: '8px',
                padding: '12px',
                textAlign: 'center',
                color: '#fff',
                minHeight: '80px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center'
              }}
            >
              <div style={{ fontSize: '11px', opacity: 0.7, marginBottom: '4px' }}>{zoneId}</div>
              {isInsufficient ? (
                <div style={{ fontSize: '13px' }}>Insufficient Data</div>
              ) : (
                <>
                  <div style={{ fontSize: '16px', fontWeight: 700 }}>{zone.state}</div>
                  <div style={{ fontSize: '11px' }}>{zone.student_count} students</div>
                  {zone.is_anomaly && (
                    <div style={{ fontSize: '11px', marginTop: '4px', color: '#fbbf24' }}>
                      {zone.anomaly_message || 'Anomaly — Please Verify'}
                    </div>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default HeatmapGrid;
