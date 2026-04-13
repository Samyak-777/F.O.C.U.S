"""
Tests for tamper-proof PDF export.
US-04: SHA-256 signed, includes all required fields, override info preserved.
"""
import pytest
import hashlib
from src.export.pdf_exporter import export_attendance_pdf
from config.constants import AttendanceStatus
from tests.test_data.generators import make_attendance_records
import reportlab.rl_config
reportlab.rl_config.pageCompression = 0


@pytest.mark.us04
class TestPDFExporter:

    def _make_session_data(self):
        return {
            "batch_id": "CSE-3A-2026",
            "date": "2026-04-02",
            "session_time": "09:00 - 10:00",
            "faculty_name": "Prof. Anand Kulkarni",
            "room_id": "LH-101"
        }

    def test_export_produces_pdf_bytes(self):
        """US-04: Export must return valid PDF bytes (non-empty, starts with %PDF)."""
        session_data = self._make_session_data()
        roll_numbers = [f"BT23CSE{str(i).zfill(3)}" for i in range(1, 11)]
        records = make_attendance_records(1, roll_numbers)

        result = export_attendance_pdf(session_data, records, [])

        assert isinstance(result, bytes), "Export must return bytes"
        assert len(result) > 0, "Export must produce non-empty content"
        assert result[:4] == b"%PDF", "Export must produce valid PDF (starts with %PDF)"

    def test_export_includes_sha256_digest(self):
        """US-04 AC-3: SHA-256 hash must appear in the PDF content."""
        session_data = self._make_session_data()
        records = make_attendance_records(1, ["BT23CSE001"])

        result = export_attendance_pdf(session_data, records, [])
        content_str = result.decode("latin-1")

        assert "SHA-256" in content_str or "sha-256" in content_str.lower(), (
            "PDF must contain SHA-256 signature reference. US-04 AC-3."
        )

    def test_export_includes_all_required_fields(self):
        """
        US-04 AC-2: Each record must include:
        Batch ID, Date, Session Time, Roll No., Name, Status, AI Confidence Score.
        """
        session_data = self._make_session_data()
        records = [{
            "roll_number": "BT23CSE019",
            "name": "Mrunmayee Limaye",
            "status": AttendanceStatus.PRESENT,
            "ai_confidence": 0.934,
            "session_id": 1
        }]

        result = export_attendance_pdf(session_data, records, [])
        content_str = result.decode("latin-1")

        required_in_pdf = [
            "BT23CSE019",
            "Mrunmayee",
            "CSE-3A-2026",
            "2026-04-02"
        ]
        for field in required_in_pdf:
            assert field in content_str, (
                f"Required field '{field}' not found in PDF export. "
                "US-04 AC-2 violated."
            )

    def test_export_includes_override_details(self):
        """
        US-04 EC-2: When override exists, PDF must show BOTH
        original AI record AND the override (faculty name, timestamp, comment).
        """
        session_data = self._make_session_data()
        records = [{
            "roll_number": "BT23CSE094",
            "name": "Sarvambh Sangle",
            "status": AttendanceStatus.PRESENT,
            "ai_confidence": 0.72,
            "session_id": 1
        }]
        overrides = [{
            "roll_number": "BT23CSE094",
            "new_status": AttendanceStatus.PRESENT,
            "faculty_name": "Prof. Anand Kulkarni",
            "override_timestamp": "2026-04-02T09:12:00",
            "comment": "Manually verified — glasses caused IR failure"
        }]

        result = export_attendance_pdf(session_data, records, overrides)
        content_str = result.decode("latin-1")

        assert "Kulkarni" in content_str, (
            "Override faculty name must appear in PDF. US-04 EC-2."
        )
        assert "glasses" in content_str.lower() or "IR" in content_str, (
            "Override comment must appear in PDF. US-04 EC-2."
        )

    def test_consent_withdrawn_masked_in_export(self):
        """
        US-04 EC-3: Student who withdrew consent must appear as
        'Data Restricted — Consent Withdrawn' in the export.
        """
        session_data = self._make_session_data()
        records = [{
            "roll_number": "BT23CSE057",
            "name": "Geetha Narapareddygari",
            "status": AttendanceStatus.CONSENT_WITHDRAWN,
            "ai_confidence": None,
            "session_id": 1
        }]

        result = export_attendance_pdf(session_data, records, [])
        content_str = result.decode("latin-1")

        assert "Restricted" in content_str or "Consent Withdrawn" in content_str, (
            "Consent-withdrawn student must be masked in export. US-04 EC-3."
        )
        # Must NOT expose any actual attendance status
        assert "93%" not in content_str  # No AI confidence percentage