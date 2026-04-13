// frontend/src/tests/AttendanceTable.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AttendanceTable } from '../components/AttendanceTable';

describe('AttendanceTable — US-02 Acceptance Criteria', () => {

  const sampleRecords = {
    'BT23CSE001': 'Present',
    'BT23CSE002': 'Unverified',
    'BT23CSE003': 'Late'
  };

  it('renders Unverified status distinctly from Absent', () => {
    /**
     * US-01/US-02: Unverified must be visually distinct from Absent.
     * Faculty must understand the difference.
     */
    render(<AttendanceTable records={sampleRecords} onOverride={vi.fn()} />);
    const unverifiedEl = screen.getByText('Unverified');
    expect(unverifiedEl).toBeTruthy();
    // Ensure there's no 'Absent' shown for Unverified records
    const rows = document.querySelectorAll('tr');
    rows.forEach(row => {
      if (row.textContent.includes('BT23CSE002')) {
        expect(row.textContent).not.toContain('Absent');
      }
    });
  });

  it('override button prompts for mandatory comment', () => {
    /**
     * US-02 EC-2: Override UI must prompt for a comment.
     */
    const mockOverride = vi.fn();
    render(<AttendanceTable records={sampleRecords} onOverride={mockOverride} />);

    const overrideBtn = screen.getAllByText(/override/i)[0];
    fireEvent.click(overrideBtn);

    // Comment input must appear
    const commentInput = screen.getByPlaceholderText(/reason|comment/i);
    expect(commentInput).toBeTruthy();
  });
});