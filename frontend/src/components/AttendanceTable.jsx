/**
 * AttendanceTable — Pure presentational component for displaying attendance records.
 * US-02: Shows status with override capability. Unverified ≠ Absent.
 * Props: { records: { rollNumber: status }, onOverride: function }
 */
import { useState } from 'react';

const STATUS_COLORS = {
  Present: '#22c55e',
  Late: '#eab308',
  Absent: '#ef4444',
  Unverified: '#f97316'
};

export function AttendanceTable({ records = {}, onOverride }) {
  const [activeOverride, setActiveOverride] = useState(null);
  const [comment, setComment] = useState('');
  const [newStatus, setNewStatus] = useState('Present');

  const entries = Object.entries(records);

  const handleOverrideClick = (roll) => {
    setActiveOverride(roll);
    setComment('');
    setNewStatus('Present');
  };

  const handleSubmitOverride = (roll) => {
    if (comment.trim().length >= 5 && onOverride) {
      onOverride({ roll_number: roll, new_status: newStatus, comment });
      setActiveOverride(null);
      setComment('');
    }
  };

  return (
    <div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #334155' }}>
            <th style={{ textAlign: 'left', padding: '8px' }}>Roll No.</th>
            <th style={{ textAlign: 'left', padding: '8px' }}>Status</th>
            <th style={{ textAlign: 'left', padding: '8px' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([roll, status]) => (
            <tr key={roll} style={{ borderBottom: '1px solid #1e293b' }}>
              <td style={{ padding: '8px' }}>{roll}</td>
              <td style={{ padding: '8px' }}>
                <span style={{
                  backgroundColor: STATUS_COLORS[status] || '#64748b',
                  color: '#fff',
                  padding: '2px 10px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: 600
                }}>
                  {status}
                </span>
              </td>
              <td style={{ padding: '8px' }}>
                <button onClick={() => handleOverrideClick(roll)} style={{
                  fontSize: '12px', cursor: 'pointer', background: 'none',
                  border: '1px solid #475569', borderRadius: '6px', padding: '4px 10px',
                  color: '#e2e8f0'
                }}>
                  Override
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {activeOverride && (
        <div style={{ marginTop: '12px', padding: '12px', border: '1px solid #475569', borderRadius: '8px' }}>
          <div style={{ marginBottom: '8px', fontSize: '13px' }}>
            Override for <strong>{activeOverride}</strong>
          </div>
          <select value={newStatus} onChange={e => setNewStatus(e.target.value)}
            style={{ marginRight: '8px', padding: '4px' }}>
            <option value="Present">Present</option>
            <option value="Late">Late</option>
            <option value="Absent">Absent</option>
          </select>
          <input
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="Reason/comment for override"
            style={{ padding: '4px 8px', marginRight: '8px', minWidth: '200px' }}
          />
          <button onClick={() => handleSubmitOverride(activeOverride)}
            disabled={comment.trim().length < 5}
            style={{ padding: '4px 12px', cursor: 'pointer' }}>
            Submit
          </button>
        </div>
      )}
    </div>
  );
}

export default AttendanceTable;
