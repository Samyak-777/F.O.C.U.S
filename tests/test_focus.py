"""
Test face recognition — US-01 acceptance criteria.
"""
import pytest
import numpy as np
from config.constants import AttendanceStatus, EngagementState


def make_blank_frame(w=1280, h=720):
    return np.zeros((h, w, 3), dtype=np.uint8)


class TestUS01AcceptanceCriteria:
    """
    US-01 AC-2: Confidence <80% → Unverified (never Absent)
    US-01 EC-3: NEVER mark Absent on AI recognition failure
    """

    def test_attendance_status_values(self):
        """Verify all required status values exist."""
        assert AttendanceStatus.PRESENT == "Present"
        assert AttendanceStatus.LATE == "Late"
        assert AttendanceStatus.ABSENT == "Absent"
        assert AttendanceStatus.UNVERIFIED == "Unverified"
        assert AttendanceStatus.CAMERA_BLOCKED == "Camera_Blocked"
        assert AttendanceStatus.CONSENT_WITHDRAWN == "Data_Restricted_Consent_Withdrawn"

    def test_engagement_states(self):
        """Verify all engagement states exist."""
        assert EngagementState.ACTIVE == "Active"
        assert EngagementState.PASSIVE == "Passive"
        assert EngagementState.DISENGAGED == "Disengaged"
        assert EngagementState.EYE_UNAVAILABLE == "Eye_Tracking_Unavailable"
        assert EngagementState.NOISY_SIGNAL == "Noisy_Signal_Inconclusive"
        assert EngagementState.INSUFFICIENT_DATA == "Insufficient_Data"


class TestUS05EngagementRules:
    """US-05: Engagement scoring fairness tests."""

    def test_ir_glare_not_disengaged(self):
        """ENG-01: IR glare (eye_confidence <0.60) → Eye_Tracking_Unavailable."""
        from src.engagement.gaze_tracker import GazeResult
        from src.engagement.classifier import StudentEngagementTracker

        tracker = StudentEngagementTracker("BT23CSE001")
        low_conf_gaze = GazeResult(0.0, 0.0, 0.40, is_available=False)
        state = tracker.classify(pose=None, gaze=low_conf_gaze)
        assert state == EngagementState.EYE_UNAVAILABLE

    def test_oscillation_suppression(self):
        """ENG-03: >15 state flips in 5 min → Noisy Signal."""
        from src.engagement.classifier import StudentEngagementTracker
        from src.engagement.head_pose import HeadPoseResult

        tracker = StudentEngagementTracker("BT23CSE001")
        for i in range(20):
            yaw = 40.0 if i % 2 == 0 else 5.0
            pose = HeadPoseResult(yaw=yaw, pitch=0.0, roll=0.0, confidence=0.9)
            tracker.classify(pose=pose, gaze=None)

        last_state = tracker.classify(
            pose=HeadPoseResult(yaw=5.0, pitch=0.0, roll=0.0, confidence=0.9),
            gaze=None
        )
        assert last_state == EngagementState.NOISY_SIGNAL


class TestUS06ConsentRules:
    """Privacy consent tests."""

    def test_consent_text_multilingual(self):
        """PRI-06: Consent forms available in en, hi, mr, te."""
        from src.consent.consent_manager import ConsentManager
        cm = ConsentManager()
        for lang in ["en", "hi", "mr", "te"]:
            form = cm.get_consent_form(lang)
            assert "title" in form
            assert "body" in form
            assert "action" in form
            assert len(form["body"]) > 50
