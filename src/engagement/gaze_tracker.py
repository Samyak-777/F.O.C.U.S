"""
Gaze direction estimation using MediaPipe iris landmarks.
No external model needed — MediaPipe iris tracking is built-in.
ENG-01: When IR glare causes eye_confidence < 0.60, mark as EYE_UNAVAILABLE.
"""
import numpy as np
from dataclasses import dataclass
from config.settings import settings

# MediaPipe iris landmark indices (only available with refine_landmarks=True)
LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
LEFT_EYE_CONTOUR = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_CONTOUR = [362, 385, 387, 263, 373, 380]


@dataclass
class GazeResult:
    gaze_x: float        # Horizontal: -1 (far left) to +1 (far right)
    gaze_y: float        # Vertical: -1 (up) to +1 (down)
    eye_confidence: float  # 0-1; below EYE_CONFIDENCE_MIN = unavailable
    is_available: bool   # False if IR glare or eye not visible


def compute_iris_gaze(face_landmarks, frame_w: int, frame_h: int) -> GazeResult:
    """
    Compute gaze direction from iris position relative to eye contour.
    Geometry-based method — no ML model needed.
    """
    try:
        def get_point(idx):
            lm = face_landmarks.landmark[idx]
            return np.array([lm.x * frame_w, lm.y * frame_h])

        def iris_center(indices):
            pts = np.array([get_point(i) for i in indices])
            return pts.mean(axis=0)

        def eye_center(indices):
            pts = np.array([get_point(i) for i in indices])
            return pts.mean(axis=0)

        left_iris_pos = iris_center(LEFT_IRIS)
        left_eye_pos = eye_center(LEFT_EYE_CONTOUR)
        left_eye_pts = np.array([get_point(i) for i in LEFT_EYE_CONTOUR])
        left_eye_width = np.linalg.norm(left_eye_pts.max(axis=0) - left_eye_pts.min(axis=0))

        right_iris_pos = iris_center(RIGHT_IRIS)
        right_eye_pos = eye_center(RIGHT_EYE_CONTOUR)
        right_eye_pts = np.array([get_point(i) for i in RIGHT_EYE_CONTOUR])
        right_eye_width = np.linalg.norm(right_eye_pts.max(axis=0) - right_eye_pts.min(axis=0))

        if left_eye_width < 1 or right_eye_width < 1:
            return GazeResult(0.0, 0.0, 0.0, False)

        left_offset = (left_iris_pos - left_eye_pos) / left_eye_width
        right_offset = (right_iris_pos - right_eye_pos) / right_eye_width

        avg_gaze_x = float((left_offset[0] + right_offset[0]) / 2)
        avg_gaze_y = float((left_offset[1] + right_offset[1]) / 2)

        eye_openness_left = left_eye_pts[:, 1].max() - left_eye_pts[:, 1].min()
        eye_openness_right = right_eye_pts[:, 1].max() - right_eye_pts[:, 1].min()
        eye_openness = float((eye_openness_left + eye_openness_right) / 2)
        eye_height = frame_h * 0.03
        eye_confidence = min(1.0, eye_openness / eye_height)

        is_available = eye_confidence >= settings.EYE_CONFIDENCE_MIN

        return GazeResult(
            gaze_x=avg_gaze_x,
            gaze_y=avg_gaze_y,
            eye_confidence=eye_confidence,
            is_available=is_available
        )

    except (IndexError, ZeroDivisionError, AttributeError):
        return GazeResult(0.0, 0.0, 0.0, False)
