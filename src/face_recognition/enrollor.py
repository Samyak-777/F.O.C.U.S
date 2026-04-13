"""
Student face enrollment. Called once per student at semester start.
Stores encrypted 512-dim ArcFace embeddings. Never stores raw images (PRI-05).
"""
import numpy as np
from pathlib import Path
from typing import List, Optional
from src.utils.crypto import encrypt_embedding
from src.utils.logger import logger
from config.settings import settings

# Initialize InsightFace model ONCE at module level (expensive)
_face_app = None


def get_face_app():
    """Lazy-load InsightFace app. Downloads buffalo_l on first call (~1.2GB)."""
    global _face_app
    if _face_app is None:
        from insightface.app import FaceAnalysis
        _face_app = FaceAnalysis(
            name="buffalo_l",
            root=str(Path("models/insightface")),
            providers=["CPUExecutionProvider"]
        )
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
        logger.info("InsightFace buffalo_l loaded successfully")
    return _face_app


def extract_embedding(image_bgr: np.ndarray) -> Optional[np.ndarray]:
    """
    Extract 512-dim ArcFace embedding from a BGR image.
    Returns None if no face is detected.
    """
    app = get_face_app()
    faces = app.get(image_bgr)
    if not faces:
        return None
    face = max(faces, key=lambda f: f.det_score)
    return face.embedding  # shape: (512,)


def enroll_student(
    roll_number: str,
    images_bgr: List[np.ndarray],
    embedding_dir: Path = Path("data/embeddings")
) -> dict:
    """
    Enroll a student by computing mean embedding from multiple photos.
    US-06: stores ONLY embeddings, never raw images.
    US-01: minimum 3 images recommended for partial occlusion robustness.
    """
    embedding_dir.mkdir(parents=True, exist_ok=True)
    successful_embeddings = []

    for i, img in enumerate(images_bgr):
        emb = extract_embedding(img)
        if emb is not None:
            successful_embeddings.append(emb)
            logger.debug(f"Enrollment image {i+1}: embedding extracted for {roll_number}")
        else:
            logger.warning(f"Enrollment image {i+1}: no face detected for {roll_number}")

    if len(successful_embeddings) < 1:
        return {"status": "failed", "reason": "No face detected in any enrollment image"}

    # Average embedding across all successful photos (more robust)
    mean_embedding = np.mean(successful_embeddings, axis=0)
    mean_embedding = mean_embedding / np.linalg.norm(mean_embedding)

    # Encrypt before saving (DPDP Act requirement)
    encrypted = encrypt_embedding(mean_embedding)
    save_path = embedding_dir / f"{roll_number}.enc"
    save_path.write_bytes(encrypted)

    logger.info(f"Student {roll_number} enrolled with {len(successful_embeddings)} embeddings")
    return {
        "status": "success",
        "roll_number": roll_number,
        "embeddings_used": len(successful_embeddings),
        "embedding_file": str(save_path)
    }


def delete_student_embedding(roll_number: str, embedding_dir: Path = Path("data/embeddings")) -> bool:
    """
    DPDP Act PRI-03: Permanently delete biometric template on consent revocation.
    Must be called within 24 hours of revocation.
    """
    path = embedding_dir / f"{roll_number}.enc"
    if path.exists():
        path.unlink()
        logger.info(f"Biometric embedding deleted for {roll_number}")
        return True
    return False
