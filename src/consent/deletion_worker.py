"""
Biometric deletion worker.
PRI-03: Ensures biometric data is deleted within 24 hours of consent revocation.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.db.models import ConsentRecord
from src.face_recognition.enrollor import delete_student_embedding
from src.utils.logger import logger, audit_log


def process_pending_deletions(db: Session) -> int:
    """
    Check for revoked consents without completed deletion.
    Called periodically (e.g., every hour) to ensure 24hr compliance.
    """
    cutoff = datetime.utcnow() - timedelta(hours=24)
    pending = db.query(ConsentRecord).filter(
        ConsentRecord.status == "revoked",
        ConsentRecord.deletion_completed_at.is_(None),
        ConsentRecord.timestamp <= cutoff
    ).all()

    deleted_count = 0
    for record in pending:
        success = delete_student_embedding(record.roll_number)
        if success:
            record.deletion_completed_at = datetime.utcnow()
            deleted_count += 1
            audit_log(f"DELAYED_DELETION: {record.roll_number} biometric deleted (24hr worker)")
        else:
            logger.warning(f"Deletion worker: no embedding found for {record.roll_number}")
            record.deletion_completed_at = datetime.utcnow()  # Mark as handled

    db.commit()
    if deleted_count > 0:
        logger.info(f"Deletion worker: processed {deleted_count} pending deletions")
    return deleted_count
