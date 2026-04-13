"""Camera management with reconnection logic."""
import cv2
from config.settings import settings
from src.utils.logger import logger


class CameraManager:
    def __init__(self):
        self.cap: cv2.VideoCapture | None = None

    def open(self, index: int = 0, fps: int = 10):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera at index {index}")
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        logger.info(f"Camera {index} opened at {fps}fps")

    def read_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        return frame if ret else None

    def close(self):
        if self.cap:
            self.cap.release()
            logger.info("Camera closed")
