/**
 * Tests for zone-wise engagement heatmap component.
 * US-03: Visual representation must respect privacy constraints.
 */
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { HeatmapGrid } from '../components/HeatmapGrid';

describe('HeatmapGrid — US-03 Acceptance Criteria', () => {

  it('renders Insufficient Data label for zones below minimum', () => {
    /**
     * US-03 EC-1: Zone with <8 students must show Insufficient Data,
     * never actual engagement state. Privacy protection.
     */
    const data = {
      zones: {
        'R1C1': {
          student_count: 5,
          insufficient_data: true,
          state: 'Insufficient_Data'
        }
      }
    };

    render(<HeatmapGrid data={data} />);
    expect(screen.getByText(/insufficient data/i)).toBeTruthy();
  });

  it('renders correct color for Active zone', () => {
    const data = {
      zones: {
        'R1C1': {
          student_count: 12,
          state: 'Active',
          active_pct: 75,
          insufficient_data: false
        }
      }
    };

    const { container } = render(<HeatmapGrid data={data} />);
    const zoneEl = container.querySelector('[title*="Active"]');
    // Active zones must use green (#22c55e)
    expect(zoneEl?.style?.backgroundColor).toBe('rgb(34, 197, 94)');
  });

  it('renders note that heatmap is faculty-only', () => {
    /**
     * US-03 peer review constraint: heatmap must visually indicate
     * it is restricted to faculty view only.
     */
    render(<HeatmapGrid data={{ zones: {} }} />);
    const note = screen.getByText(/faculty only/i);
    expect(note).toBeTruthy();
  });

  it('does not render individual student data', () => {
    /**
     * Privacy invariant: no roll number, no name, no individual score
     * must appear anywhere in the heatmap component.
     */
    const data = {
      zones: {
        'R1C1': {
          student_count: 10,
          state: 'Active',
          active_pct: 70,
          insufficient_data: false
        }
      }
    };

    const { container } = render(<HeatmapGrid data={data} />);
    // BT23CSE pattern must NOT appear in rendered output
    expect(container.textContent).not.toMatch(/BT\d{2}CSE\d{3}/);
  });

  it('shows anomaly warning for flagged zones', () => {
    /**
     * US-03 EC-2: 0% engagement zone must show anomaly warning.
     */
    const data = {
      zones: {
        'R2C2': {
          student_count: 15,
          state: 'Disengaged',
          active_pct: 0,
          passive_pct: 0,
          disengaged_pct: 0,
          is_anomaly: true,
          anomaly_message: 'Anomaly — Please Verify',
          insufficient_data: false
        }
      }
    };

    render(<HeatmapGrid data={data} />);
    expect(screen.getByText(/anomaly/i)).toBeTruthy();
  });
});


