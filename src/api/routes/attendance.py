"""
Attendance endpoints — override with mandatory comment (ATT-05).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_faculty_user, get_db
from src.db.crud import override_attendance

router = APIRouter()


class OverrideRequest(BaseModel):
    roll_number: str
    session_id: str
    new_status: str
    comment: str

    @field_validator("comment")
    @classmethod
    def comment_must_be_meaningful(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("Override comment is mandatory and must be at least 5 characters")
        return v.strip()


@router.post("/override")
def override(
    req: OverrideRequest,
    faculty=Depends(get_current_faculty_user),
    db: Session = Depends(get_db)
):
    """
    Override attendance status. Writes to immutable audit log (ATT-06).
    Both original AI record and override are preserved.
    """
    try:
        result = override_attendance(
            db,
            roll_number=req.roll_number,
            session_id=req.session_id,
            new_status=req.new_status,
            faculty_id=faculty.id,
            comment=req.comment
        )
        return {"status": "overridden", "record": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/session/{session_id}")
def get_session_attendance(
    session_id: int,
    faculty=Depends(get_current_faculty_user),
    db: Session = Depends(get_db)
):
    """HM-02: Get all attendance records for a session (Faculty only)."""
    from src.db.models import AttendanceRecord
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session_id
    ).all()
    return [
        {
            "roll_number": r.roll_number,
            "status": r.status,
            "ai_confidence": r.ai_confidence,
            "marked_at": r.marked_at.isoformat() if r.marked_at else None,
            "is_overridden": r.is_overridden
        }
        for r in records
    ]
