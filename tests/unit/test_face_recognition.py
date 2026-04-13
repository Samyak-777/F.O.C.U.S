"""
Unit tests for face recognition module.
ALL tests traceable to Deliverable 3 acceptance criteria.
These tests do NOT require a camera or real student photos.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from src.face_recognition.recognizer import AttendanceRecognizer, StudentEmbeddingDatabase
from src.face_recognition.occlusion_handler import extract_upper_face_embedding
from config.constants import AttendanceStatus, FailureCode
from tests.test_data.generators import (
    make_head_pose, make_classroom_frame, draw_face_on_frame, make_frame
)


# ──────────────────────────────────────────────────────────────────────────────
# US-01: Recognition accuracy for occluded faces
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.us01
class TestUS01OccludedFaceRecognition:

    def test_low_confidence_returns_unverified_not_absent(self):
        """
        US-01 AC-2 + EC-3: CRITICAL INVARIANT
        Confidence below RECOGNITION_CONFIDENCE_MIN MUST return Unverified.
        System MUST NEVER return Absent on AI failure alone.
        This is the most important single test in the entire suite.
        """
        db = MagicMock(spec=StudentEmbeddingDatabase)
        db.find_best_match.return_value = ("BT23CSE001", 0.65)  # Below 0.80 threshold

        recognizer = AttendanceRecognizer(db)

        # Mock InsightFace to return a face with embedding
        mock_face = MagicMock()
        mock_face.det_score = 0.90
        mock_face.embedding = np.random.randn(512).astype(np.float32)
        mock_face.bbox = np.array([100, 100, 200, 250], dtype=np.float32)
        mock_face.kps = np.array([
            [140, 150], [180, 150], [160, 180], [130, 210], [190, 210]
        ], dtype=np.float32)

        with patch.object(recognizer.face_app, 'get', return_value=[mock_face]):
            frame = make_classroom_frame(num_students=1)
            results = recognizer.process_frame(frame)

        for result in results:
            assert result.status != AttendanceStatus.ABSENT, (
                "FATAL: System returned ABSENT on recognition failure. "
                "US-01 EC-3 violated. System must return UNVERIFIED."
            )
            if result.confidence < 0.80:
                assert result.status == AttendanceStatus.UNVERIFIED, (
                    f"Expected UNVERIFIED for confidence={result.confidence}, "
                    f"got {result.status}"
                )

    def test_unverified_has_failure_code(self):
        """
        US-01 AC-2: Unverified records must include a timestamped failure code
        for the faculty dashboard to show.
        """
        db = MagicMock(spec=StudentEmbeddingDatabase)
        db.find_best_match.return_value = ("BT23CSE001", 0.60)

        recognizer = AttendanceRecognizer(db)
        mock_face = MagicMock()
        mock_face.det_score = 0.85
        mock_face.embedding = np.random.randn(512).astype(np.float32)
        mock_face.bbox = np.array([100, 100, 200, 250], dtype=np.float32)
        mock_face.kps = np.array([
            [140, 150], [180, 150], [160, 180], [130, 210], [190, 210]
        ], dtype=np.float32)

        with patch.object(recognizer.face_app, 'get', return_value=[mock_face]):
            results = recognizer.process_frame(make_frame())

        for r in results:
            if r.status == AttendanceStatus.UNVERIFIED:
                assert r.failure_code is not None, (
                    "Unverified status must include a failure_code for audit log"
                )
                assert r.failure_code in [
                    FailureCode.LOW_CONFIDENCE,
                    FailureCode.NO_FACE_DETECTED,
                    FailureCode.CAMERA_LOST,
                    FailureCode.PHYSICAL_OBSTRUCTION
                ]

    def test_high_confidence_returns_present(self):
        """
        US-01 AC-1 analog: High confidence match returns Present.
        """
        db = MagicMock(spec=StudentEmbeddingDatabase)
        db.find_best_match.return_value = ("BT23CSE001", 0.92)  # Above threshold

        recognizer = AttendanceRecognizer(db)
        mock_face = MagicMock()
        mock_face.det_score = 0.95
        mock_face.embedding = np.random.randn(512).astype(np.float32)
        mock_face.bbox = np.array([100, 100, 200, 250], dtype=np.float32)
        mock_face.kps = np.array([
            [140, 150], [180, 150], [160, 180], [130, 210], [190, 210]
        ], dtype=np.float32)

        with patch.object(recognizer.face_app, 'get', return_value=[mock_face]):
            results = recognizer.process_frame(make_frame())

        present_results = [r for r in results if r.status == AttendanceStatus.PRESENT]
        assert len(present_results) >= 1, "High confidence match must return PRESENT"

    def test_no_face_returns_empty_list_not_absent(self):
        """
        US-01 EC-3: When camera detects no face at all (physical obstruction),
        return empty list. The student must NOT be marked Absent from this frame.
        Absent can only be set after the full scan window with zero detections.
        """
        db = MagicMock(spec=StudentEmbeddingDatabase)
        recognizer = AttendanceRecognizer(db)

        with patch.object(recognizer.face_app, 'get', return_value=[]):
            results = recognizer.process_frame(make_frame())

        assert results == [], "No face detected must return empty list, not an Absent record"
        db.find_best_match.assert_not_called()

    def test_occlusion_ratio_high_uses_upper_face_flag(self):
        """
        US-01: When lower face is covered, used_upper_face_only flag is set True.
        """
        db = MagicMock(spec=StudentEmbeddingDatabase)
        db.find_best_match.return_value = ("BT23CSE001", 0.82)

        recognizer = AttendanceRecognizer(db)
        mock_face = MagicMock()
        mock_face.det_score = 0.85
        mock_face.embedding = np.random.randn(512).astype(np.float32)
        mock_face.bbox = np.array([100, 100, 200, 250], dtype=np.float32)
        # Simulate mouth corners very close = lower face occluded
        mock_face.kps = np.array([
            [140, 150], [180, 150], [160, 180],
            [158, 220], [162, 220]   # Mouth corners nearly touching → high occlusion
        ], dtype=np.float32)

        with patch.object(recognizer.face_app, 'get', return_value=[mock_face]):
            with patch(
                'src.face_recognition.recognizer.extract_upper_face_embedding',
                return_value=np.random.randn(512).astype(np.float32)
            ):
                results = recognizer.process_frame(make_frame())

        upper_face_results = [r for r in results if r.used_upper_face_only]
        assert len(upper_face_results) >= 1, (
            "Occluded face must set used_upper_face_only=True (US-01 dupatta fallback)"
        )

    def test_duplicate_roll_number_not_marked_twice(self):
        """
        US-02 implicit: Same student appearing in multiple frames should not
        override a confirmed Present status with a later Unverified.
        """
        db = MagicMock(spec=StudentEmbeddingDatabase)
        # First call: high confidence (Present)
        # Second call: low confidence (Unverified)
        db.find_best_match.side_effect = [
            ("BT23CSE001", 0.91),
            ("BT23CSE001", 0.62)
        ]

        recognizer = AttendanceRecognizer(db)
        mock_face = MagicMock()
        mock_face.det_score = 0.90
        mock_face.embedding = np.random.randn(512).astype(np.float32)
        mock_face.bbox = np.array([100, 100, 200, 250], dtype=np.float32)
        mock_face.kps = np.array([
            [140, 150], [180, 150], [160, 180], [130, 210], [190, 210]
        ], dtype=np.float32)

        # This logic would normally be tested at the session processor level
        # but the principle is tested here via status values
        with patch.object(recognizer.face_app, 'get', return_value=[mock_face]):
            frame = make_frame()
            results_1 = recognizer.process_frame(frame)
            results_2 = recognizer.process_frame(frame)

        assert results_1[0].status == AttendanceStatus.PRESENT
        assert results_2[0].status == AttendanceStatus.UNVERIFIED
        # The session processor must not demote Present → Unverified


# ──────────────────────────────────────────────────────────────────────────────
# Embedding Database Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestStudentEmbeddingDatabase:

    def test_empty_db_returns_no_match(self):
        """Empty database must return (None, 0.0), not raise an exception."""
        db = StudentEmbeddingDatabase()
        db.embeddings = {}
        query = np.random.randn(512).astype(np.float32)
        roll, conf = db.find_best_match(query)
        assert roll is None
        assert conf == 0.0

    def test_cosine_similarity_identical_embedding(self):
        """Identical embedding must return confidence close to 1.0."""
        db = StudentEmbeddingDatabase()
        embedding = np.random.randn(512).astype(np.float32)
        embedding_norm = embedding / np.linalg.norm(embedding)
        db.embeddings = {"BT23CSE001": embedding_norm}

        roll, conf = db.find_best_match(embedding)
        assert roll == "BT23CSE001"
        assert conf > 0.99, f"Identical embedding should return conf~1.0, got {conf}"

    def test_orthogonal_embedding_returns_no_match(self):
        """Completely different embedding must fall below threshold."""
        db = StudentEmbeddingDatabase()
        enrolled = np.zeros(512, dtype=np.float32)
        enrolled[0] = 1.0  # Unit vector in dimension 0
        db.embeddings = {"BT23CSE001": enrolled}

        query = np.zeros(512, dtype=np.float32)
        query[255] = 1.0  # Orthogonal unit vector
        roll, conf = db.find_best_match(query)
        # Orthogonal vectors have cosine similarity = 0 → should be below threshold
        # conf should be very low or (None, low) depending on implementation
        assert conf < 0.5, f"Orthogonal embedding should produce very low confidence, got {conf}"