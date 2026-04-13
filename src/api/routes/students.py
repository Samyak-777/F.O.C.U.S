"""
Student portal endpoints.
ENG-05: Students can view & contest engagement within 24hrs.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_student_user, get_db
from src.db.crud import get_student_attendance, get_student_engagement, create_contest_record
from src.consent.consent_manager import ConsentManager

router = APIRouter()
consent_manager = ConsentManager()


@router.get("/me/attendance")
def my_attendance(
    student=Depends(get_current_student_user),
    db: Session = Depends(get_db)
):
    """View my attendance records."""
    return get_student_attendance(db, student.roll_number)


@router.get("/me/engagement/{session_id}")
def my_engagement(
    session_id: str,
    student=Depends(get_current_student_user),
    db: Session = Depends(get_db)
):
    """ENG-05: View session engagement classification summary."""
    return get_student_engagement(db, student.roll_number, session_id)


class ContestRequest(BaseModel):
    reason: str


@router.post("/me/contest/{session_id}")
def contest_engagement(
    session_id: str,
    req: ContestRequest,
    student=Depends(get_current_student_user),
    db: Session = Depends(get_db)
):
    """ENG-05: Contest engagement classification."""
    record = create_contest_record(db, student.roll_number, session_id, req.reason)
    return {"status": "submitted", "contest_id": record.id}


class ConsentRequest(BaseModel):
    language: str = "en"
    guardian_signed: bool = False


@router.post("/me/consent/give")
def give_consent(
    req: ConsentRequest,
    student=Depends(get_current_student_user),
    db: Session = Depends(get_db)
):
    """PRI-01: Give explicit consent."""
    return consent_manager.give_consent(
        db, student.roll_number, req.language, "localhost",
        student.is_minor, req.guardian_signed
    )


@router.post("/me/consent/revoke")
def revoke_consent(
    student=Depends(get_current_student_user),
    db: Session = Depends(get_db)
):
    """PRI-02: Revoke consent in ≤2 clicks."""
    return consent_manager.revoke_consent(db, student.roll_number, "localhost")


@router.get("/me/consent/form")
def get_consent_form(language: str = "en"):
    """PRI-06: Get consent form in requested language."""
    return consent_manager.get_consent_form(language)
