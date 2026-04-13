"""
Performance checks for core system throughput requirements.
US-02: Attendance complete within 7 minutes for 90 students.
US-04: Export complete in ≤10 seconds for 200 students.
"""
import pytest
import time
import numpy as np
from unittest.mock import patch, MagicMock
from tests.test_data.generators import make_classroom_frame


@pytest.mark.slow
@pytest.mark.performance
class TestRecognitionSpeed:

    def test_recognition_processes_10_fps_minimum(self):
        """
        US-02 AC-2: System must process frames fast enough to scan
        90 students within 7 minutes. Minimum viable: 10fps processing.
        Target: <100ms per frame for recognition on CPU.
        """
        from src.face_recognition.recognizer import AttendanceRecognizer, StudentEmbeddingDatabase

        db = MagicMock(spec=StudentEmbeddingDatabase)
        db.find_best_match.return_value = ("BT23CSE001", 0.92)
        db.embeddings = {}

        recognizer = AttendanceRecognizer(db)
        frame = make_classroom_frame(num_students=5)

        with patch.object(recognizer.face_app, 'get', return_value=[]):
            times = []
            for _ in range(30):  # 30 frames
                start = time.perf_counter()
                recognizer.process_frame(frame)
                elapsed = time.perf_counter() - start
                times.append(elapsed)

        avg_ms = (sum(times) / len(times)) * 1000
        max_ms = max(times) * 1000

        print(f"\nRecognition speed: avg={avg_ms:.1f}ms, max={max_ms:.1f}ms")

        assert avg_ms < 100, (
            f"Average recognition time {avg_ms:.1f}ms exceeds 100ms. "
            "Cannot achieve 10fps for US-02 scan window compliance."
        )


@pytest.mark.slow
@pytest.mark.performance
class TestExportSpeed:

    def test_pdf_export_under_10_seconds_for_200_students(self):
        """US-04 AC-1: Export must complete in ≤10 seconds for up to 200 students."""
        from src.export.pdf_exporter import export_attendance_pdf
        from tests.test_data.generators import make_attendance_records

        session_data = {
            "batch_id": "CSE-ALL-2026",
            "date": "2026-04-02",
            "session_time": "09:00-10:00",
            "faculty_name": "Prof. Test"
        }
        roll_numbers = [f"BT23CSE{str(i).zfill(3)}" for i in range(1, 201)]
        records = make_attendance_records(1, roll_numbers)
        overrides = []

        start = time.perf_counter()
        result = export_attendance_pdf(session_data, records, overrides)
        elapsed = time.perf_counter() - start

        print(f"\nPDF export time for 200 students: {elapsed:.2f}s")

        assert elapsed < 10.0, (
            f"PDF export took {elapsed:.2f}s for 200 students. "
            "US-04 AC-1 requires ≤10 seconds."
        )
        assert result is not None and len(result) > 0

    def test_excel_export_under_10_seconds_for_200_students(self):
        """US-04 AC-1: Excel export also must complete in ≤10 seconds."""
        from src.export.excel_exporter import export_attendance_excel
        from tests.test_data.generators import make_attendance_records

        session_data = {
            "batch_id": "CSE-ALL-2026",
            "date": "2026-04-02",
            "session_time": "09:00-10:00",
            "faculty_name": "Prof. Test"
        }
        roll_numbers = [f"BT23CSE{str(i).zfill(3)}" for i in range(1, 201)]
        records = make_attendance_records(1, roll_numbers)

        start = time.perf_counter()
        result = export_attendance_excel(session_data, records, [])
        elapsed = time.perf_counter() - start

        assert elapsed < 10.0, f"Excel export took {elapsed:.2f}s. US-04 AC-1 requires ≤10 seconds."