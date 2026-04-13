// frontend/src/tests/ConsentForm.test.jsx
/**
 * Tests for multilingual consent form component.
 * US-06: Explicit, non-pre-checked, available in 4 languages.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ConsentForm from '../components/ConsentForm';

describe('ConsentForm — US-06 Acceptance Criteria', () => {

  it('consent checkbox is unchecked by default', () => {
    /**
     * US-06 EC-3 CRITICAL: Default state must ALWAYS be unconsented.
     * Checkbox must NEVER be pre-checked.
     */
    render(<ConsentForm language="en" onConsent={vi.fn()} />);
    const checkbox = screen.getByRole('checkbox', { name: /consent/i });
    expect(checkbox.checked).toBe(false);
  });

  it('submit button is disabled until checkbox is checked', () => {
    /**
     * US-06: Enrollment cannot proceed without explicit affirmative action.
     */
    render(<ConsentForm language="en" onConsent={vi.fn()} />);
    const submitBtn = screen.getByRole('button', { name: /give.*consent|submit|enroll/i });
    expect(submitBtn.disabled).toBe(true);
  });

  it('submit button enables after checkbox is checked', () => {
    render(<ConsentForm language="en" onConsent={vi.fn()} />);
    const checkbox = screen.getByRole('checkbox', { name: /consent/i });
    fireEvent.click(checkbox);
    const submitBtn = screen.getByRole('button', { name: /give.*consent|submit|enroll/i });
    expect(submitBtn.disabled).toBe(false);
  });

  it('renders form body text in Hindi when language is hi', () => {
    /**
     * US-06 AC-1: Consent form must render in student's preferred language.
     */
    render(<ConsentForm language="hi" onConsent={vi.fn()} />);
    // Hindi text must be present — check for Devanagari script
    const formText = document.body.textContent;
    expect(formText).toMatch(/[\u0900-\u097F]/); // Unicode block for Devanagari
  });

  it('calls onConsent with correct language when submitted', () => {
    const mockOnConsent = vi.fn();
    render(<ConsentForm language="mr" onConsent={mockOnConsent} />);

    fireEvent.click(screen.getByRole('checkbox', { name: /consent/i }));
    fireEvent.click(screen.getByRole('button', { name: /give.*consent|submit|enroll/i }));

    expect(mockOnConsent).toHaveBeenCalledWith(expect.objectContaining({
      language: 'mr'
    }));
  });
});


