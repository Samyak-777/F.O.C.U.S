"""
Phone detection using YOLOv8n COCO pre-trained model.
Model downloads automatically on first use (~6MB for yolov8n.pt).
"""
from ultralytics import YOLO
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from config.settings import settings
from src.utils.logger import logger

_yolo_model: Optional[YOLO] = None


def get_yolo_model() -> YOLO:
    global _yolo_model
    if _yolo_model is None:
        model_path = Path("models/yolov8n.pt")
        _yolo_model = YOLO(str(model_path) if model_path.exists() else "yolov8n.pt")
        logger.info("YOLOv8n loaded (COCO pre-trained)")
    return _yolo_model


@dataclass
class PhoneDetection:
    bbox: tuple
    confidence: float
    zone: Optional[str]


class PhoneDetector:
    """
    Detects mobile phones in classroom video frames.
    Only triggers alerts after PHONE_SUSTAINED_SECONDS of continuous detection.
    """

    def __init__(self):
        self.model = get_yolo_model()
        self._active_detections: dict = {}
        self._phone_class_id = settings.PHONE_CLASS_ID

    def detect(self, frame_bgr: np.ndarray, timestamp: float) -> List[PhoneDetection]:
        """Run YOLOv8 inference. Returns only phones visible for sustained duration."""
        results = self.model(
            frame_bgr,
            classes=[self._phone_class_id],
            conf=settings.PHONE_CONFIDENCE_THRESHOLD,
            verbose=False
        )

        confirmed_detections = []
        current_bboxes = []

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id != self._phone_class_id:
                    continue

                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                bbox = (x1, y1, x2, y2)
                center_key = (round((x1 + x2) / 40) * 20, round((y1 + y2) / 40) * 20)
                current_bboxes.append(center_key)

                if center_key not in self._active_detections:
                    self._active_detections[center_key] = timestamp

                first_seen = self._active_detections[center_key]
                duration = timestamp - first_seen

                if duration >= settings.PHONE_SUSTAINED_SECONDS:
                    confirmed_detections.append(PhoneDetection(
                        bbox=bbox, confidence=conf, zone=None
                    ))

        # Clean up detections that are no longer visible
        gone_keys = [k for k in self._active_detections if k not in current_bboxes]
        for k in gone_keys:
            del self._active_detections[k]

        return confirmed_detections
