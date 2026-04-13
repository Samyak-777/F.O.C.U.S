"""
Maps pixel coordinates to classroom zones.
HM-01: minimum 8 students per zone. Zones with <8 are merged.
"""
from typing import Tuple, Optional


class ZoneMapper:
    """Divides camera frame into a grid of classroom zones."""

    def __init__(self, rows: int = 4, cols: int = 3):
        self.rows = rows
        self.cols = cols
        self.total_zones = rows * cols

    def get_zone_for_bbox(self, bbox: Tuple[int, int, int, int], frame_shape: Tuple) -> str:
        """Map a bounding box center to a zone ID like 'R2C1'."""
        h, w = frame_shape[:2]
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        row = min(int(cy / h * self.rows), self.rows - 1)
        col = min(int(cx / w * self.cols), self.cols - 1)
        return f"R{row+1}C{col+1}"

    def get_zone_for_landmarks(self, face_landmarks, frame_shape) -> Optional[str]:
        """Map MediaPipe face landmarks to a zone."""
        try:
            h, w = frame_shape[:2]
            nose = face_landmarks.landmark[1]
            cx = nose.x * w
            cy = nose.y * h
            row = min(int(cy / h * self.rows), self.rows - 1)
            col = min(int(cx / w * self.cols), self.cols - 1)
            return f"R{row+1}C{col+1}"
        except Exception:
            return None
