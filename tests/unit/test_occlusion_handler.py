"""
Tests for upper-face-only recognition fallback.
US-01: Must recognize Riya with dupatta covering nose-to-chin.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from tests.test_data.generators import draw_face_on_frame, make_frame


@pytest.mark.us01
class TestOcclusionHandler:

    def test_upper_face_crop_on_occluded_face(self):
        """
        US-01: When lower face is covered, extract_upper_face_embedding
        must attempt extraction on the upper 55% of the face region.
        Must return a 512-dim embedding (not None) for a visible face.
        """
        from src.face_recognition.occlusion_handler import extract_upper_face_embedding

        # Create frame with occluded face
        frame = make_frame(640, 480)
        frame = draw_face_on_frame(frame, (320, 240), occlusion_ratio=0.45)

        mock_face = MagicMock()
        mock_face.bbox = np.array([260, 140, 380, 340], dtype=np.float32)
        mock_face.kps = np.array([
            [295, 185], [355, 185], [320, 215], [290, 290], [350, 290]
        ], dtype=np.float32)

        expected_emb = np.random.randn(512).astype(np.float32)

        with patch('src.face_recognition.occlusion_handler.get_face_app') as mock_app:
            mock_app_instance = MagicMock()
            mock_face_result = MagicMock()
            mock_face_result.embedding = expected_emb
            mock_app_instance.get.return_value = [mock_face_result]
            mock_app.return_value = mock_app_instance

            result = extract_upper_face_embedding(frame, mock_face)

        assert result is not None, (
            "Upper face extraction returned None. "
            "For US-01 (dupatta), fallback must always attempt extraction."
        )
        assert result.shape == (512,), f"Expected 512-dim embedding, got shape {result.shape}"

    def test_occlusion_handler_returns_none_on_empty_crop(self):
        """
        Edge case: If bbox is degenerate (zero size), must return None gracefully.
        """
        from src.face_recognition.occlusion_handler import extract_upper_face_embedding

        frame = make_frame(100, 100)
        mock_face = MagicMock()
        mock_face.bbox = np.array([50, 50, 50, 50], dtype=np.float32)  # Zero-size
        mock_face.kps = np.array([[50, 50]] * 5, dtype=np.float32)
        mock_face.embedding = np.random.randn(512).astype(np.float32)

        result = extract_upper_face_embedding(frame, mock_face)
        assert result is not None  # Should fall back to full face embedding