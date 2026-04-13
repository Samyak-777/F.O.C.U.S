"""
Real-time face recognition for attendance marking during class sessions.
Implements US-01, US-02 acceptance criteria exactly.
"""
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from src.utils.crypto import decrypt_embedding
from src.face_recognition.enrollor import get_face_app, extract_embedding
from src.face_recognition.occlusion_handler import extract_upper_face_embedding
from config.settings import settings
from config.constants import AttendanceStatus, FailureCode
from src.utils.logger import logger


@dataclass
class RecognitionResult:
    roll_number: Optional[str]
    confidence: float
    status: str
    failure_code: Optional[str]
    face_bbox: Optional[Tuple]
    used_upper_face_only: bool = False


class StudentEmbeddingDatabase:
    """In-memory store of all enrolled student embeddings for fast cosine search."""

    def __init__(self, embedding_dir: Path = Path("data/embeddings")):
        self.embedding_dir = embedding_dir
        self.embeddings: Dict[str, np.ndarray] = {}

    def load_all(self):
        """Load and decrypt all enrolled embeddings into memory at session start."""
        self.embeddings.clear()
        if not self.embedding_dir.exists():
            logger.warning(f"Embedding directory {self.embedding_dir} does not exist")
            return
        for enc_file in self.embedding_dir.glob("*.enc"):
            roll = enc_file.stem
            try:
                emb = decrypt_embedding(enc_file.read_bytes())
                self.embeddings[roll] = emb / np.linalg.norm(emb)
            except Exception as e:
                logger.error(f"Failed to load embedding for {roll}: {e}")
        
        if not self.embeddings:
            if not settings.EMBEDDING_ENCRYPTION_KEY:
                logger.error("EMBEDDING_ENCRYPTION_KEY is missing in .env! Cannot decrypt enrollments.")
            else:
                logger.warning("No student embeddings could be loaded. Ensure students are enrolled.")
        
        logger.info(f"Loaded {len(self.embeddings)} student embeddings")

    def find_best_match(self, query_embedding: np.ndarray) -> Tuple[Optional[str], float]:
        """Cosine similarity search against all enrolled embeddings."""
        if not self.embeddings:
            return None, 0.0

        query_norm = query_embedding / np.linalg.norm(query_embedding)
        best_roll = None
        best_similarity = -1.0

        for roll, enrolled_emb in self.embeddings.items():
            similarity = float(np.dot(query_norm, enrolled_emb))
            if similarity > best_similarity:
                best_similarity = similarity
                best_roll = roll

        distance = 1.0 - best_similarity
        confidence = max(0.0, 1.0 - (distance / settings.RECOGNITION_DISTANCE_MAX))

        if distance > settings.RECOGNITION_DISTANCE_MAX:
            return None, confidence

        return best_roll, min(confidence, 1.0)


class AttendanceRecognizer:
    """Main class: processes a video frame → returns RecognitionResult per detected face."""

    def __init__(self, db: StudentEmbeddingDatabase):
        self.db = db
        self.face_app = get_face_app()

    def process_frame(self, frame_bgr: np.ndarray) -> List[RecognitionResult]:
        """
        Process one video frame. Returns a list of RecognitionResult,
        one per detected face.

        Logic per US-01:
        - Full face → normal recognition
        - Lower face occluded → upper face fallback
        - Confidence < RECOGNITION_CONFIDENCE_MIN → Unverified (NOT Absent) [ATT-01]
        - No face detected → return empty list
        """
        results = []
        faces = self.face_app.get(frame_bgr)

        if not faces:
            return results

        for face in faces:
            bbox = tuple(face.bbox.astype(int))
            det_score = float(face.det_score)

            occlusion_ratio = self._estimate_lower_face_occlusion(face)

            if occlusion_ratio > 0.5:
                query_emb = extract_upper_face_embedding(frame_bgr, face)
                used_upper = True
                logger.debug(f"Using upper-face fallback (occlusion={occlusion_ratio:.2f})")
            else:
                query_emb = face.embedding
                used_upper = False

            if query_emb is None:
                results.append(RecognitionResult(
                    roll_number=None,
                    confidence=0.0,
                    status=AttendanceStatus.UNVERIFIED,
                    failure_code=FailureCode.NO_FACE_DETECTED,
                    face_bbox=bbox,
                    used_upper_face_only=used_upper
                ))
                continue

            roll, confidence = self.db.find_best_match(query_emb)

            if confidence >= settings.RECOGNITION_CONFIDENCE_MIN and roll is not None:
                results.append(RecognitionResult(
                    roll_number=roll,
                    confidence=confidence,
                    status=AttendanceStatus.PRESENT,
                    failure_code=None,
                    face_bbox=bbox,
                    used_upper_face_only=used_upper
                ))
            else:
                # CRITICAL ATT-01: NEVER mark Absent on recognition failure
                results.append(RecognitionResult(
                    roll_number=roll,
                    confidence=confidence,
                    status=AttendanceStatus.UNVERIFIED,
                    failure_code=FailureCode.LOW_CONFIDENCE,
                    face_bbox=bbox,
                    used_upper_face_only=used_upper
                ))

        return results

    def _estimate_lower_face_occlusion(self, face) -> float:
        """Estimate ratio of lower face that is occluded."""
        try:
            kps = face.kps
            if kps is None or len(kps) < 5:
                return 0.0
            left_mouth = kps[3]
            right_mouth = kps[4]
            mouth_width = abs(right_mouth[0] - left_mouth[0])
            face_width = abs(face.bbox[2] - face.bbox[0])
            if face_width < 1:
                return 0.0
            ratio = mouth_width / face_width
            return max(0.0, 1.0 - (ratio / 0.3))
        except Exception:
            return 0.0
