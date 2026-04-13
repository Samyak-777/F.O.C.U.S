"""Phone alert endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_faculty_user, get_db
from src.db.models import PhoneAlert

router = APIRouter()


@router.get("/{session_id}")
def get_alerts(
    session_id: str,
    faculty=Depends(get_current_faculty_user),
    db: Session = Depends(get_db)
):
    """Get all phone alerts for a session."""
    alerts = db.query(PhoneAlert).filter(
        PhoneAlert.session_id == int(session_id)
    ).order_by(PhoneAlert.detected_at.desc()).all()

    return [
        {
            "id": a.id,
            "zone_id": a.zone_id,
            "confidence": a.confidence,
            "detected_at": a.detected_at.isoformat() if a.detected_at else None,
            "acknowledged": a.acknowledged_by_faculty
        }
        for a in alerts
    ]
