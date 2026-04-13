"""Engagement heatmap endpoint — faculty only (HM-02)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_faculty_user, get_db
from src.db.models import EngagementRecord

router = APIRouter()


@router.get("/heatmap/{session_id}")
def get_heatmap(
    session_id: str,
    faculty=Depends(get_current_faculty_user),
    db: Session = Depends(get_db)
):
    """HM-02: Faculty-only heatmap view."""
    records = db.query(EngagementRecord).filter(
        EngagementRecord.session_id == int(session_id)
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail="No engagement data for this session")

    zones = {}
    for r in records:
        zones[r.zone_id] = {
            "student_count": r.student_count,
            "active_pct": r.active_pct,
            "passive_pct": r.passive_pct,
            "disengaged_pct": r.disengaged_pct,
            "insufficient_data": r.insufficient_data,
            "is_merged_zone": r.is_merged_zone,
            "expires_at": r.expires_at.isoformat() if r.expires_at else None
        }

    return {"session_id": session_id, "zones": zones}
