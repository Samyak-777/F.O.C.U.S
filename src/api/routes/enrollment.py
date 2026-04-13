"""
Face enrollment API routes.
US-01: Students enroll by capturing 3+ face images via webcam.
US-06: Only after explicit consent. Stores only encrypted embeddings (PRI-05).
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
from sqlalchemy.orm import Session
import numpy as np
import cv2
from src.api.dependencies import get_current_student_user, get_db
from src.face_recognition.enrollor import enroll_student, delete_student_embedding
from src.db.models import User, ConsentRecord
from src.db.crud import get_latest_consent
from src.utils.logger import logger

router = APIRouter()


@router.post("/face")
async def enroll_face(
    images: List[UploadFile] = File(..., description="3+ face images for enrollment"),
    student: User = Depends(get_current_student_user),
    db: Session = Depends(get_db)
):
    """
    Enroll a student's face by uploading 3+ images.

    Flow:
    1. Verify consent exists
    2. Read uploaded images → BGR numpy arrays
    3. Extract 512-dim ArcFace embeddings via InsightFace
    4. Average + normalize embeddings
    5. Encrypt (Fernet AES) and save as data/embeddings/{roll}.enc
    6. Raw images are NEVER stored (PRI-05)
    """
    # Step 1: Verify consent
    consent = get_latest_consent(db, student.roll_number)

    if not consent or consent.status != "given":
        raise HTTPException(
            status_code=403,
            detail="Consent required before enrollment. Please give consent first (US-06)."
        )

    # Step 2: Validate image count (minimum 3 for occlusion robustness)
    if len(images) < 3:
        raise HTTPException(
            status_code=422,
            detail=f"Minimum 3 images required for robust enrollment (US-01). Got {len(images)}."
        )

    if len(images) > 10:
        raise HTTPException(
            status_code=422,
            detail="Maximum 10 images allowed per enrollment."
        )

    # Step 3: Convert uploaded files to BGR numpy arrays
    images_bgr = []
    for i, img_file in enumerate(images):
        contents = await img_file.read()
        if not contents:
            continue
        img_array = np.frombuffer(contents, dtype=np.uint8)
        img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img_bgr is None:
            logger.warning(f"Enrollment image {i+1} could not be decoded for {student.roll_number}")
            continue
        images_bgr.append(img_bgr)

    if len(images_bgr) < 1:
        raise HTTPException(
            status_code=422,
            detail="No valid images could be decoded. Ensure images are JPEG/PNG format."
        )

    # Step 4: Run enrollment (extract embeddings, encrypt, save)
    result = enroll_student(student.roll_number, images_bgr)

    if result["status"] == "failed":
        raise HTTPException(
            status_code=422,
            detail=f"Enrollment failed: {result['reason']}. Try better lighting or face the camera directly."
        )

    logger.info(f"Student {student.roll_number} enrolled via API ({result['embeddings_used']} embeddings)")

    return {
        "status": "enrolled",
        "roll_number": student.roll_number,
        "embeddings_used": result["embeddings_used"],
        "message": f"Face enrolled successfully using {result['embeddings_used']} images. "
                   f"Your face data is stored as an encrypted embedding only — no raw images are saved."
    }


@router.get("/status")
def enrollment_status(
    student: User = Depends(get_current_student_user),
    db: Session = Depends(get_db)
):
    """Check if student's face is enrolled."""
    from pathlib import Path
    embedding_path = Path("data/embeddings") / f"{student.roll_number}.enc"
    is_enrolled = embedding_path.exists()

    consent = get_latest_consent(db, student.roll_number)
    has_consent = consent is not None and consent.status == "given"

    return {
        "roll_number": student.roll_number,
        "is_enrolled": is_enrolled,
        "has_consent": has_consent,
        "embedding_file": str(embedding_path) if is_enrolled else None
    }


@router.delete("/face")
def delete_enrollment(
    student: User = Depends(get_current_student_user),
):
    """
    Delete enrolled face data. Called when consent is revoked.
    DPDP Act PRI-03: Must complete within 24 hours.
    """
    deleted = delete_student_embedding(student.roll_number)
    if deleted:
        return {"status": "deleted", "message": "Your biometric data has been permanently deleted."}
    else:
        return {"status": "not_found", "message": "No enrollment data found for your account."}
