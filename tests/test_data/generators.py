"""
Utilities for generating synthetic test data.
No real student faces. No camera required.
All images are programmatically generated.
"""
import numpy as np
import cv2
import mediapipe as mp
from dataclasses import dataclass
from typing import List, Tuple
from src.engagement.head_pose import HeadPoseResult
from src.engagement.gaze_tracker import GazeResult


# ── Synthetic face frame generators ──────────────────────────────────────────

def make_frame(width=1280, height=720, background_lux: int = 400) -> np.ndarray:
    """
    Generate a synthetic classroom frame.
    background_lux: approximate lux simulation via gray value
    - 400 lux = standard classroom lighting
    - 150 lux = dim (edge case)
    - 600 lux = bright
    """
    gray_value = min(255, int(background_lux * 0.4))
    return np.ones((height, width, 3), dtype=np.uint8) * gray_value


def draw_face_on_frame(
    frame: np.ndarray,
    center: Tuple[int, int],
    occlusion_ratio: float = 0.0,
    glasses: bool = False,
    head_tilt_deg: float = 0.0
) -> np.ndarray:
    """
    Draw a synthetic face for testing occlusion and recognition pipelines.

    Args:
        center: (cx, cy) pixel position
        occlusion_ratio: 0.0 = no occlusion, 0.5 = lower half covered (dupatta)
        glasses: draw rectangular glasses frame
        head_tilt_deg: apply rotation to simulate head tilt
    """
    frame = frame.copy()
    cx, cy = center
    face_color = (220, 185, 155)  # Medium-brown skin tone

    # Draw face ellipse
    cv2.ellipse(frame, (cx, cy), (60, 80), head_tilt_deg, 0, 360, face_color, -1)

    # Eyes
    cv2.ellipse(frame, (cx - 22, cy - 25), (14, 8), 0, 0, 360, (255, 255, 255), -1)
    cv2.ellipse(frame, (cx + 22, cy - 25), (14, 8), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(frame, (cx - 22, cy - 25), 6, (40, 40, 40), -1)   # Pupils
    cv2.circle(frame, (cx + 22, cy - 25), 6, (40, 40, 40), -1)

    if glasses:
        # Draw thick glasses frame to simulate IR reflections
        cv2.rectangle(frame, (cx - 38, cy - 35), (cx - 6, cy - 15), (80, 80, 80), 3)
        cv2.rectangle(frame, (cx + 6, cy - 35), (cx + 38, cy - 15), (80, 80, 80), 3)
        # Bridge
        cv2.line(frame, (cx - 6, cy - 25), (cx + 6, cy - 25), (80, 80, 80), 2)

    # Apply occlusion (cover lower face as dupatta/scarf would)
    if occlusion_ratio > 0:
        occlusion_start_y = int(cy - 80 * (1.0 - occlusion_ratio))
        covering_color = (0, 100, 180)  # Dupatta blue/colored fabric
        cv2.rectangle(
            frame,
            (cx - 70, occlusion_start_y),
            (cx + 70, cy + 80),
            covering_color, -1
        )

    return frame


def make_classroom_frame(
    num_students: int = 10,
    frame_width: int = 1280,
    frame_height: int = 720,
    include_occluded: bool = False,
    include_glasses: bool = False
) -> np.ndarray:
    """
    Generate a synthetic multi-student classroom frame.
    Students are evenly distributed across the frame.
    """
    frame = make_frame(frame_width, frame_height, background_lux=400)
    positions = []
    cols = min(5, num_students)
    rows = (num_students + cols - 1) // cols

    for i in range(num_students):
        row = i // cols
        col = i % cols
        cx = int((col + 0.5) * frame_width / cols)
        cy = int((row + 0.5) * frame_height / rows)
        positions.append((cx, cy))

    for idx, pos in enumerate(positions):
        occluded = include_occluded and (idx % 3 == 0)
        glasses_on = include_glasses and (idx % 4 == 0)
        frame = draw_face_on_frame(
            frame, pos,
            occlusion_ratio=0.45 if occluded else 0.0,
            glasses=glasses_on
        )

    return frame


# ── Synthetic pose / gaze data generators ────────────────────────────────────

def make_head_pose(
    yaw: float = 0.0,
    pitch: float = 0.0,
    roll: float = 0.0,
    confidence: float = 0.9
) -> HeadPoseResult:
    return HeadPoseResult(yaw=yaw, pitch=pitch, roll=roll, confidence=confidence)


def make_gaze(
    gaze_x: float = 0.0,
    gaze_y: float = 0.0,
    eye_confidence: float = 0.85,
    is_available: bool = True
) -> GazeResult:
    return GazeResult(
        gaze_x=gaze_x,
        gaze_y=gaze_y,
        eye_confidence=eye_confidence,
        is_available=is_available
    )


# State scenario builders for engagement testing
def scenario_active_student() -> Tuple[HeadPoseResult, GazeResult]:
    """Student looking at board, good gaze tracking."""
    return make_head_pose(yaw=5.0, pitch=-5.0), make_gaze(0.0, 0.0, 0.90)


def scenario_note_taking() -> Tuple[HeadPoseResult, GazeResult]:
    """Student looking down — should be Passive, NOT Disengaged."""
    return make_head_pose(yaw=3.0, pitch=-28.0), make_gaze(0.0, 0.3, 0.75)


def scenario_glasses_glare() -> Tuple[HeadPoseResult, GazeResult]:
    """Arjun Nair scenario: IR glare → eye confidence 0.40 (below threshold)."""
    return make_head_pose(yaw=5.0, pitch=-5.0), make_gaze(0.0, 0.0, 0.40, is_available=False)


def scenario_phone_user() -> Tuple[HeadPoseResult, GazeResult]:
    """Head down, not note-taking — actual disengagement."""
    return make_head_pose(yaw=5.0, pitch=-40.0), make_gaze(0.3, 0.5, 0.70)


def scenario_turned_away() -> Tuple[HeadPoseResult, GazeResult]:
    """Student turned 45° to talk to neighbor."""
    return make_head_pose(yaw=45.0, pitch=0.0), make_gaze(0.8, 0.0, 0.80)


# ── Attendance record factories ───────────────────────────────────────────────

def make_attendance_records(
    session_id: int,
    roll_numbers: List[str],
    statuses: List[str] = None
) -> List[dict]:
    """Generate a list of attendance record dicts for testing exports."""
    from config.constants import AttendanceStatus
    import random
    default_statuses = [AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.ABSENT]

    records = []
    for i, roll in enumerate(roll_numbers):
        status = statuses[i] if statuses else random.choice(default_statuses)
        records.append({
            "roll_number": roll,
            "name": f"Student {i+1}",
            "session_id": session_id,
            "status": status,
            "ai_confidence": round(0.70 + random.random() * 0.30, 3),
            "failure_code": None
        })
    return records