"""
Upper-face-only recognition fallback for students with religious head coverings.
US-01: Must recognize using eyes, eyebrows, nose bridge only.
"""
import numpy as np
import cv2
from src.face_recognition.enrollor import get_face_app


def extract_upper_face_embedding(frame_bgr: np.ndarray, face) -> np.ndarray | None:
    """
    Extract an embedding using ONLY upper facial region (eyes to nose bridge).
    Used as fallback when lower face is covered (dupatta, scarf, mask).
    """
    try:
        bbox = face.bbox.astype(int)
        x1, y1, x2, y2 = bbox
        face_h = y2 - y1
        # Crop to upper 55% of face (forehead to nose bridge)
        upper_y2 = y1 + int(face_h * 0.55)
        upper_crop = frame_bgr[y1:upper_y2, x1:x2]
        if upper_crop.size == 0:
            return face.embedding

        # Resize to 112x112 (InsightFace expected input)
        resized = cv2.resize(upper_crop, (112, 112))
        full_size = np.zeros((112, 112, 3), dtype=np.uint8)
        full_size[:112, :] = resized

        app = get_face_app()
        faces = app.get(full_size)
        if faces:
            return faces[0].embedding
        return face.embedding  # Return full-face embedding as last resort
    except Exception:
        return None
