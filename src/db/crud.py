"""
Database CRUD operations.
All write operations to audit tables are append-only (no updates/deletes).
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from src.db.models import (
    User, UserRole, ConsentRecord, ClassSession,
    AttendanceRecord, AttendanceAuditLog, EngagementRecord,
    PhoneAlert, ContestRecord, ExportLog
)
from src.utils.logger import audit_log
from config.settings import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── User CRUD ──

def create_user(db: Session, name: str, email: str, password: str,
                role: UserRole = UserRole.STUDENT,
                roll_number: Optional[str] = None,
                is_minor: bool = False) -> User:
    user = User(
        name=name,
        email=email,
        hashed_password=pwd_context.hash(password),
        role=role,
        roll_number=roll_number,
        is_minor=is_minor
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_roll(db: Session, roll_number: str) -> Optional[User]:
    return db.query(User).filter(User.roll_number == roll_number).first()


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Session CRUD ──

def create_session(db: Session, batch_id: str, faculty_id: int,
                   scheduled_start: datetime) -> ClassSession:
    session = ClassSession(
        batch_id=batch_id,
        faculty_id=faculty_id,
        scheduled_start=scheduled_start,
        actual_start=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: int) -> Optional[ClassSession]:
    return db.query(ClassSession).filter(ClassSession.id == session_id).first()


def update_session(db: Session, session_id: int, updates: dict):
    db.query(ClassSession).filter(ClassSession.id == session_id).update(updates)
    db.commit()


# ── Attendance CRUD ──

def create_attendance_record(db: Session, session_id: int, roll_number: str,
                              status: str, ai_confidence: float,
                              failure_code: Optional[str] = None,
                              used_upper_face: bool = False) -> AttendanceRecord:
    record = AttendanceRecord(
        session_id=session_id,
        roll_number=roll_number,
        status=status,
        ai_confidence=ai_confidence,
        failure_code=failure_code,
        used_upper_face=used_upper_face
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_attendance_record(db: Session, session_id: int,
                           roll_number: str) -> Optional[AttendanceRecord]:
    return db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session_id,
        AttendanceRecord.roll_number == roll_number
    ).first()


def override_attendance(db: Session, roll_number: str, session_id: str,
                         new_status: str, faculty_id: int, comment: str) -> dict:
    """
    Override attendance with mandatory comment (ATT-05).
    Preserves original in immutable audit log (ATT-06).
    """
    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == int(session_id),
        AttendanceRecord.roll_number == roll_number
    ).first()

    if not record:
        raise ValueError(f"No attendance record found for {roll_number} in session {session_id}")

    # Get faculty name for audit
    faculty = db.query(User).filter(User.id == faculty_id).first()
    faculty_name = faculty.name if faculty else f"faculty_{faculty_id}"

    # Create immutable audit log entry
    audit_entry = AttendanceAuditLog(
        attendance_id=record.id,
        session_id=int(session_id),
        roll_number=roll_number,
        original_status=record.status,
        original_ai_confidence=record.ai_confidence,
        new_status=new_status,
        faculty_id=faculty_id,
        faculty_name=faculty_name,
        comment=comment
    )
    db.add(audit_entry)

    # Update main record
    record.status = new_status
    record.is_overridden = True
    db.commit()

    audit_log(
        f"ATTENDANCE_OVERRIDE: {roll_number} session={session_id} "
        f"{record.status}→{new_status} by {faculty_name}: {comment}"
    )

    return {
        "roll_number": roll_number,
        "original_status": audit_entry.original_status,
        "new_status": new_status,
        "overridden_by": faculty_name,
        "comment": comment
    }


def get_student_attendance(db: Session, roll_number: str) -> List[dict]:
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.roll_number == roll_number
    ).order_by(AttendanceRecord.marked_at.desc()).all()
    return [
        {
            "session_id": r.session_id,
            "status": r.status,
            "ai_confidence": r.ai_confidence,
            "marked_at": r.marked_at.isoformat() if r.marked_at else None,
            "is_overridden": r.is_overridden
        }
        for r in records
    ]


def sync_session_attendance(db: Session, session_id: int,
                            attendance_dict: dict):
    """
    Sync in-memory attendance results to the database.
    Uses 'upsert' logic: updates if exists, creates if not.
    attendance_dict: {roll_number: {"status": str, "confidence": float, ...}}
    """
    for roll, details in attendance_dict.items():
        # Handle cases where details might just be a status string (legacy)
        if isinstance(details, str):
            status = details
            confidence = None
            failure_code = None
            used_upper = False
        else:
            status = details.get("status")
            confidence = details.get("confidence")
            failure_code = details.get("failure_code")
            used_upper = details.get("used_upper", False)

        record = get_attendance_record(db, session_id, roll)
        if record:
            # Only update if status changed or it was unverified and now present
            if record.status != status or (record.ai_confidence or 0) < (confidence or 0):
                record.status = status
                record.ai_confidence = confidence
                record.failure_code = failure_code
                record.used_upper_face = used_upper
        else:
            create_attendance_record(
                db, session_id, roll, status, confidence,
                failure_code, used_upper
            )
    db.commit()


def get_student_engagement(db: Session, session_id: int) -> dict:
    """Get engagement data for a session (zone-level). HM-02."""
    records = db.query(EngagementRecord).filter(
        EngagementRecord.session_id == session_id
    ).all()
    return {
        "session_id": session_id,
        "zones": {
            r.zone_id: {
                "student_count": r.student_count,
                "active_pct": r.active_pct,
                "passive_pct": r.passive_pct,
                "disengaged_pct": r.disengaged_pct,
                "insufficient_data": r.insufficient_data
            }
            for r in records
        }
    }


def save_engagement_records(db: Session, session_id: int, zones_dict: dict):
    """
    US-03, HM-01: Save zone-wise engagement heatmap data.
    zones_dict should be the 'zones' part of the heatmap calculation.
    """
    # Clear existing if any (idempotency)
    db.query(EngagementRecord).filter(EngagementRecord.session_id == session_id).delete()
    
    for zone_id, data in zones_dict.items():
        if data.get("insufficient_data"):
            # Still save but mark as insufficient
            record = EngagementRecord(
                session_id=session_id,
                zone_id=zone_id,
                student_count=data["student_count"],
                active_pct=0.0,
                passive_pct=0.0,
                disengaged_pct=0.0,
                insufficient_data=True,
                expires_at=datetime.utcnow() + timedelta(days=settings.HEATMAP_RETENTION_DAYS)
            )
        else:
            record = EngagementRecord(
                session_id=session_id,
                zone_id=zone_id,
                student_count=data["student_count"],
                active_pct=data["active_pct"],
                passive_pct=data["passive_pct"],
                disengaged_pct=data["disengaged_pct"],
                insufficient_data=False,
                expires_at=datetime.utcnow() + timedelta(days=settings.HEATMAP_RETENTION_DAYS)
            )
        db.add(record)
    db.commit()


# ── Alert CRUD ──

def create_phone_alert(db: Session, session_id: int, zone_id: str, 
                       confidence: float) -> PhoneAlert:
    alert = PhoneAlert(
        session_id=session_id,
        zone_id=zone_id,
        confidence=confidence,
        detected_at=datetime.utcnow()
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


# ── Consent CRUD ──

def create_consent_record(db: Session, roll_number: str, status: str,
                           language: str, ip: str,
                           guardian_signed: bool = False) -> ConsentRecord:
    record = ConsentRecord(
        roll_number=roll_number,
        status=status,
        language=language,
        ip_address=ip,
        guardian_countersignature=guardian_signed
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    audit_log(f"CONSENT_{status.upper()}: {roll_number} lang={language}")
    return record


def get_latest_consent(db: Session, roll_number: str) -> Optional[ConsentRecord]:
    return db.query(ConsentRecord).filter(
        ConsentRecord.roll_number == roll_number
    ).order_by(desc(ConsentRecord.timestamp)).first()


def update_consent_deletion(db: Session, roll_number: str, deletion_time: datetime):
    latest = get_latest_consent(db, roll_number)
    if latest and latest.status == "revoked":
        latest.deletion_completed_at = deletion_time
        db.commit()


# ── Contest CRUD ──

def create_contest_record(db: Session, roll_number: str, session_id: str,
                           reason: str) -> ContestRecord:
    record = ContestRecord(
        roll_number=roll_number,
        session_id=int(session_id),
        reason=reason
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ── Export CRUD ──

def log_export_action(db: Session, admin_id: int, batch_id: str,
                       format: str, record_count: int) -> ExportLog:
    log = ExportLog(
        admin_id=admin_id,
        batch_id=batch_id,
        format=format,
        record_count=record_count
    )
    db.add(log)
    db.commit()
    audit_log(f"EXPORT: batch={batch_id} format={format} records={record_count} by admin={admin_id}")
    return log


def get_batch_attendance(db: Session, batch_id: str) -> Tuple[list, list, dict]:
    """Get all attendance records for a batch, with overrides and session data."""
    sessions = db.query(ClassSession).filter(
        ClassSession.batch_id == batch_id
    ).order_by(ClassSession.actual_start.desc()).all()
    
    if not sessions:
        return [], [], {}

    session = sessions[0]  # Get the LATEST session
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id
    ).all()

    # Get overrides
    overrides = db.query(AttendanceAuditLog).filter(
        AttendanceAuditLog.session_id == session.id
    ).all()

    # Build records list with user names
    result_records = []
    for r in records:
        user = db.query(User).filter(User.roll_number == r.roll_number).first()
        result_records.append({
            "roll_number": r.roll_number,
            "name": user.name if user else r.roll_number,
            "status": r.status,
            "ai_confidence": r.ai_confidence,
            "failure_code": r.failure_code
        })

    override_list = [
        {
            "roll_number": o.roll_number,
            "new_status": o.new_status,
            "faculty_name": o.faculty_name,
            "comment": o.comment
        }
        for o in overrides
    ]

    faculty = db.query(User).filter(User.id == session.faculty_id).first()
    session_data = {
        "batch_id": batch_id,
        "date": session.scheduled_start.strftime("%Y-%m-%d") if session.scheduled_start else "",
        "session_time": session.scheduled_start.strftime("%H:%M") if session.scheduled_start else "",
        "room_id": session.room_id or "",
        "faculty_name": faculty.name if faculty else ""
    }

    return result_records, override_list, session_data


# ── Heatmap cleanup ──

def delete_expired_engagement_records(db: Session) -> int:
    """US-03: Auto-delete engagement records past their expiry date."""
    expired = db.query(EngagementRecord).filter(
        EngagementRecord.expires_at <= datetime.utcnow()
    ).all()
    count = len(expired)
    for r in expired:
        db.delete(r)
    db.commit()
    if count > 0:
        audit_log(f"HEATMAP_CLEANUP: Deleted {count} expired engagement records")
    return count
