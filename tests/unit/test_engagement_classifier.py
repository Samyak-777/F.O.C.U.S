"""
Unit tests for engagement state classifier.
Every test directly maps to a US-05 acceptance criterion or edge case.
"""
import pytest
import time
from src.engagement.classifier import StudentEngagementTracker
from config.constants import EngagementState
from config.settings import settings
from tests.test_data.generators import (
    make_head_pose, make_gaze,
    scenario_active_student, scenario_note_taking,
    scenario_glasses_glare, scenario_phone_user, scenario_turned_away
)


@pytest.mark.us05
class TestEngagementClassifier:

    def setup_method(self):
        self.tracker = StudentEngagementTracker("BT23CSE004")

    def test_forward_gaze_returns_active(self):
        """US-05 AC-1: Student looking forward → Active state."""
        pose, gaze = scenario_active_student()
        state = self.tracker.classify(pose, gaze)
        assert state == EngagementState.ACTIVE, (
            f"Forward-facing student classified as {state}, expected ACTIVE"
        )

    def test_ir_glare_returns_eye_unavailable_not_disengaged(self):
        """
        US-05 AC-2: IR glare (eye_confidence < 0.60) must return
        EYE_TRACKING_UNAVAILABLE, never DISENGAGED.
        Arjun Nair: worn anti-reflective coating causes IR glare.
        """
        pose, low_conf_gaze = scenario_glasses_glare()
        assert low_conf_gaze.eye_confidence < settings.EYE_CONFIDENCE_MIN, (
            "Test setup error: gaze confidence should be below threshold"
        )

        state = self.tracker.classify(pose, low_conf_gaze)

        assert state != EngagementState.DISENGAGED, (
            "FATAL: IR glare classified as DISENGAGED. "
            "US-05 AC-2 violated. Must return EYE_TRACKING_UNAVAILABLE."
        )
        assert state == EngagementState.EYE_UNAVAILABLE, (
            f"IR glare must return EYE_UNAVAILABLE, got {state}"
        )

    def test_note_taking_within_120s_is_not_disengaged(self):
        """
        US-05 AC-1: Looking down for < 2 continuous minutes is NOT Disengaged.
        Note-taking is an active behavior the model must not penalize.
        """
        pose, gaze = scenario_note_taking()
        # pose.pitch = -28° (below threshold) but within 120s grace period
        state = self.tracker.classify(pose, gaze)

        assert state != EngagementState.DISENGAGED, (
            "Note-taking (head down <120s) classified as DISENGAGED. "
            "US-05 AC-1 violated."
        )
        assert state in [EngagementState.ACTIVE, EngagementState.PASSIVE]

    def test_sustained_head_down_over_120s_is_disengaged(self):
        """
        US-05: After 120s of continuous head-down, should classify as Disengaged.
        The 2-minute grace period for note-taking has expired.
        """
        tracker = StudentEngagementTracker("BT23CSE004")
        pose, gaze = scenario_phone_user()  # -40° pitch (steeper than note-taking)

        # Force state_start_time to 125 seconds ago
        tracker.state_start_time = time.time() - 125
        tracker.current_state = EngagementState.PASSIVE

        state = tracker.classify(pose, gaze)
        assert state == EngagementState.DISENGAGED, (
            f"After 125s head-down, expected DISENGAGED, got {state}"
        )

    def test_oscillation_suppression_noisy_signal(self):
        """
        US-05 EC-1: More than 15 state flips in 5-minute window → Noisy Signal.
        Not contributing to engagement tally.
        """
        tracker = StudentEngagementTracker("BT23CSE001")

        # Generate 20 rapid state flips
        for i in range(20):
            if i % 2 == 0:
                pose = make_head_pose(yaw=40.0)  # Disengaged
                gaze = make_gaze(0.8, 0.0, 0.80)
            else:
                pose = make_head_pose(yaw=5.0)   # Active
                gaze = make_gaze(0.0, 0.0, 0.90)
            tracker.classify(pose, gaze)

        # The 21st call should return NOISY_SIGNAL
        final_pose = make_head_pose(yaw=5.0)
        final_gaze = make_gaze(0.0, 0.0, 0.90)
        state = tracker.classify(final_pose, final_gaze)

        assert state == EngagementState.NOISY_SIGNAL, (
            f"After 20+ rapid state flips, expected NOISY_SIGNAL, got {state}"
        )

    def test_no_face_returns_social_occlusion(self):
        """
        US-05 EC-2: When face is blocked by a neighboring student,
        classify as SOCIAL_OCCLUSION, not DISENGAGED.
        """
        state = self.tracker.classify(pose=None, gaze=None)
        assert state == EngagementState.SOCIAL_OCCLUSION, (
            f"Missing face must return SOCIAL_OCCLUSION, got {state}"
        )

    def test_turned_away_returns_disengaged(self):
        """US-05: Student turned 45° away → Disengaged (yaw > threshold)."""
        pose, gaze = scenario_turned_away()
        assert abs(pose.yaw) > settings.YAW_DISENGAGED_THRESHOLD

        state = self.tracker.classify(pose, gaze)
        assert state == EngagementState.DISENGAGED

    def test_session_summary_eye_unavailable_over_50pct_is_insufficient(self):
        """
        US-05 EC-3: If eye tracking unavailable for >50% of session,
        student's engagement is Insufficient Data.
        Arjun Nair: consistent glasses glare all session.
        """
        tracker = StudentEngagementTracker("BT23CSE004")
        pose = make_head_pose(yaw=5.0)

        # Simulate 60 samples: 40 EYE_UNAVAILABLE + 20 ACTIVE
        for _ in range(40):
            tracker.classify(pose, make_gaze(0.0, 0.0, 0.40, is_available=False))
        for _ in range(20):
            tracker.classify(pose, make_gaze(0.0, 0.0, 0.90, is_available=True))

        summary = tracker.get_session_summary()

        assert summary["state"] == EngagementState.INSUFFICIENT_DATA, (
            "When eye tracking unavailable >50% of session, "
            "must return INSUFFICIENT_DATA. US-05 EC-3 violated."
        )
        assert summary.get("reason") == "eye_tracking_unavailable_over_50pct"

    def test_session_summary_normal_produces_percentages(self):
        """Session summary with normal data must include percentage breakdowns."""
        tracker = StudentEngagementTracker("BT23CSE001")
        pose = make_head_pose(yaw=5.0)
        gaze = make_gaze(0.0, 0.0, 0.90)

        for _ in range(30):
            tracker.classify(pose, gaze)

        summary = tracker.get_session_summary()
        assert "active_pct" in summary
        assert "passive_pct" in summary
        assert "disengaged_pct" in summary
        total = summary["active_pct"] + summary["passive_pct"] + summary["disengaged_pct"]
        assert abs(total - 100.0) < 1.0, f"Percentages must sum to ~100%, got {total}"


@pytest.mark.us05
class TestHeadPoseThresholds:
    """Verify all threshold constants produce correct state transitions."""

    def test_yaw_within_passive_threshold_is_active(self):
        tracker = StudentEngagementTracker("TEST")
        pose = make_head_pose(yaw=settings.YAW_PASSIVE_THRESHOLD - 1)
        gaze = make_gaze(0.0, 0.0, 0.90)
        assert tracker.classify(pose, gaze) == EngagementState.ACTIVE

    def test_yaw_at_passive_boundary_is_passive(self):
        tracker = StudentEngagementTracker("TEST")
        pose = make_head_pose(yaw=settings.YAW_PASSIVE_THRESHOLD + 1)
        gaze = make_gaze(0.0, 0.0, 0.90)
        assert tracker.classify(pose, gaze) == EngagementState.PASSIVE

    def test_yaw_beyond_disengaged_threshold_is_disengaged(self):
        tracker = StudentEngagementTracker("TEST")
        pose = make_head_pose(yaw=settings.YAW_DISENGAGED_THRESHOLD + 5)
        gaze = make_gaze(0.0, 0.0, 0.90)
        assert tracker.classify(pose, gaze) == EngagementState.DISENGAGED