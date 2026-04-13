"""
Engagement state classifier.
Implements US-05 acceptance criteria exactly:
- 3 states: Active, Passive, Disengaged
- IR glare → EYE_UNAVAILABLE (not Disengaged) [ENG-01]
- Note-taking (head down <120s) → not Disengaged [ENG-02]
- Oscillation suppression (>15 flips/5min → Noisy Signal) [ENG-03]
- Eye tracking unavailable >50% → Insufficient Data [ENG-04]
"""
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional
from src.engagement.head_pose import HeadPoseResult
from src.engagement.gaze_tracker import GazeResult
from config.settings import settings
from config.constants import EngagementState


@dataclass
class EngagementSample:
    timestamp: float
    state: str


class StudentEngagementTracker:
    """
    Per-student engagement tracker. One instance per student per session.
    Maintains a rolling window of samples for oscillation detection.
    """

    def __init__(self, roll_number: str):
        self.roll_number = roll_number
        self.samples: Deque[EngagementSample] = deque()
        self.current_state: str = EngagementState.ACTIVE
        self.state_start_time: float = time.time()
        self.state_transitions: Deque[float] = deque()

    def classify(self, pose: Optional[HeadPoseResult], gaze: Optional[GazeResult]) -> str:
        """Classify current engagement state based on head pose and gaze."""
        now = time.time()

        # ENG-01: Eye tracking unavailable (IR glare)
        if gaze is not None and not gaze.is_available:
            raw_state = EngagementState.EYE_UNAVAILABLE
        # No face detected (social occlusion or temp blockage)
        elif pose is None:
            raw_state = EngagementState.SOCIAL_OCCLUSION
        else:
            abs_yaw = abs(pose.yaw)
            pitch = pose.pitch

            if abs_yaw <= settings.YAW_PASSIVE_THRESHOLD:
                raw_state = EngagementState.ACTIVE
            elif abs_yaw <= settings.YAW_DISENGAGED_THRESHOLD:
                raw_state = EngagementState.PASSIVE
            else:
                raw_state = EngagementState.DISENGAGED

            # ENG-02: head down (note-taking) ≤120s is NOT Disengaged
            if pitch < -settings.PITCH_DOWN_THRESHOLD:
                time_in_current = now - self.state_start_time
                if time_in_current <= 120:
                    raw_state = EngagementState.PASSIVE
                else:
                    raw_state = EngagementState.DISENGAGED

        # State transition tracking
        if raw_state != self.current_state:
            self.state_transitions.append(now)
            self.current_state = raw_state
            self.state_start_time = now

        # Prune transitions older than FLIP_SUPPRESSION_WINDOW
        cutoff = now - settings.FLIP_SUPPRESSION_WINDOW
        while self.state_transitions and self.state_transitions[0] < cutoff:
            self.state_transitions.popleft()

        # ENG-03: >15 transitions in 5min → Noisy Signal
        if len(self.state_transitions) > settings.FLIP_SUPPRESSION_MAX:
            return EngagementState.NOISY_SIGNAL

        self.samples.append(EngagementSample(timestamp=now, state=raw_state))
        return raw_state

    def get_session_summary(self) -> dict:
        """
        Compute session-level engagement summary.
        ENG-04: If eye tracking unavailable >50% of session → Insufficient Data.
        """
        if not self.samples:
            return {"state": EngagementState.INSUFFICIENT_DATA, "samples": 0}

        total = len(self.samples)
        counts = {s: 0 for s in [
            EngagementState.ACTIVE, EngagementState.PASSIVE,
            EngagementState.DISENGAGED, EngagementState.EYE_UNAVAILABLE,
            EngagementState.NOISY_SIGNAL
        ]}
        for sample in self.samples:
            if sample.state in counts:
                counts[sample.state] += 1

        eye_unavailable_ratio = counts[EngagementState.EYE_UNAVAILABLE] / total

        if eye_unavailable_ratio > 0.50:
            return {
                "state": EngagementState.INSUFFICIENT_DATA,
                "reason": "eye_tracking_unavailable_over_50pct",
                "samples": total
            }

        dominant_state = max(
            [EngagementState.ACTIVE, EngagementState.PASSIVE, EngagementState.DISENGAGED],
            key=lambda s: counts[s]
        )

        return {
            "state": dominant_state,
            "active_pct": round(counts[EngagementState.ACTIVE] / total * 100, 1),
            "passive_pct": round(counts[EngagementState.PASSIVE] / total * 100, 1),
            "disengaged_pct": round(counts[EngagementState.DISENGAGED] / total * 100, 1),
            "samples": total
        }
