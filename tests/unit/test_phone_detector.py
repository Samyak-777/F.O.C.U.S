"""
Tests for YOLOv8 phone detection.
Risk analysis from AI-REQ-3: false positives carry severe consequences in exam context.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.detection.phone_detector import PhoneDetector, PhoneDetection
from config.settings import settings


@pytest.mark.ai_model
class TestPhoneDetector:

    def setup_method(self):
        self.detector = PhoneDetector()

    def test_phone_only_alerted_after_sustained_duration(self):
        """
        AI-REQ-3 risk mitigation: A phone visible for less than
        PHONE_SUSTAINED_SECONDS must NOT trigger an alert.
        This prevents false positives from brief occlusions.
        """
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        # Mock YOLO to always detect a phone
        mock_box = MagicMock()
        mock_box.cls = [67]
        mock_box.conf = [0.85]
        mock_box.xyxy = [np.array([100, 100, 200, 200])]

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]

        self.detector.model = MagicMock(return_value=[mock_result])
        if True:
            # Detection at t=0.0 — should NOT alert yet
            result_t0 = self.detector.detect(frame, timestamp=0.0)
            assert result_t0 == [], (
                f"Phone visible for 0s must not alert. Got {len(result_t0)} alerts."
            )

            # Detection at t=2.0 — still below PHONE_SUSTAINED_SECONDS (5s)
            result_t2 = self.detector.detect(frame, timestamp=2.0)
            assert result_t2 == [], (
                f"Phone visible for 2s (< {settings.PHONE_SUSTAINED_SECONDS}s) must not alert."
            )

            # Detection at t=6.0 — ABOVE threshold, should alert
            result_t6 = self.detector.detect(frame, timestamp=6.0)
            assert len(result_t6) >= 1, (
                f"Phone visible for 6s (> {settings.PHONE_SUSTAINED_SECONDS}s) must trigger alert."
            )

    def test_phone_disappears_resets_timer(self):
        """
        If a phone disappears and reappears, the timer must reset.
        Prevents gradual accumulation from brief repeated appearances.
        """
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        mock_box = MagicMock()
        mock_box.cls = [67]
        mock_box.conf = [0.85]
        mock_box.xyxy = [np.array([100, 100, 200, 200])]
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]

        empty_result = MagicMock()
        empty_result.boxes = []

        self.detector.model = MagicMock()
        if True:
            # Phone seen at t=0 and t=3 (below threshold)
            self.detector.model.return_value = [mock_result]
            self.detector.detect(frame, timestamp=0.0)
            self.detector.detect(frame, timestamp=3.0)

            # Phone disappears at t=3.5
            self.detector.model.return_value = [empty_result]
            self.detector.detect(frame, timestamp=3.5)

            # Phone reappears at t=4.0 — timer should have reset
            self.detector.model.return_value = [mock_result]
            result = self.detector.detect(frame, timestamp=4.0)
            assert result == [], (
                "Timer must reset when phone disappears. "
                "Reappeared phone at t=4.0 should not alert (only 0.5s visible after reset)."
            )

    def test_low_confidence_phone_not_detected(self):
        """
        AI-REQ-3: Detections below PHONE_CONFIDENCE_THRESHOLD must be ignored.
        Prevents false alerts from low-quality detections (textbooks, calculators).
        """
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        mock_box = MagicMock()
        mock_box.cls = [67]
        mock_box.conf = [settings.PHONE_CONFIDENCE_THRESHOLD - 0.05]  # Below threshold
        mock_box.xyxy = [np.array([100, 100, 200, 200])]
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]

        self.detector.model = MagicMock(return_value=[mock_result])
        if True:
            # Even after 10 seconds, low-confidence detection must not alert
            result = self.detector.detect(frame, timestamp=10.0)
            assert result == [], (
                "Low confidence detection must never alert. "
                "Risk: textbooks, calculators falsely flagged in exams."
            )

    def test_non_phone_class_ignored(self):
        """Only COCO class 67 (cell phone) should trigger alerts."""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        mock_box = MagicMock()
        mock_box.cls = [73]   # Class 73 = laptop — not a phone
        mock_box.conf = [0.95]
        mock_box.xyxy = [np.array([100, 100, 300, 300])]
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]

        self.detector.model = MagicMock(return_value=[mock_result])
        if True:
            result = self.detector.detect(frame, timestamp=10.0)
            assert result == [], "Non-phone class must not trigger phone alert"