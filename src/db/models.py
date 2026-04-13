"""
SQLAlchemy ORM models.
All tables are append-only where indicated — no DELETE or UPDATE on audit records.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
import enum


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"
    PRIVACY_OFFICER = "privacy_officer"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.STUDENT)
    preferred_language = Column(String, default="en")  # US-06
    is_minor = Column(Boolean, default=False)           # US-06 edge case !1
    guardian_consent_obtained = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConsentRecord(Base):
    """
    US-06: Every consent action is recorded immutably.
    status: 'given' | 'revoked'
    """
    __tablename__ = "consent_records"
    id = Column(Integer, primary_key=True)
    roll_number = Column(String, ForeignKey("users.roll_number"), nullable=False, index=True)
    status = Column(String, nullable=False)     # 'given' or 'revoked'
    language = Column(String, nullable=False)   # language of consent form shown
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String)
    guardian_countersignature = Column(Boolean, default=False)
    deletion_completed_at = Column(DateTime, nullable=True)  # Set after 24hr deletion


class ClassSession(Base):
    __tablename__ = "class_sessions"
    id = Column(Integer, primary_key=True)
    batch_id = Column(String, nullable=False, index=True)
    faculty_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(String)
    scheduled_start = Column(DateTime, nullable=False)
    actual_start = Column(DateTime)
    ended_at = Column(DateTime)
    status = Column(String, default="active")  # active | completed | incomplete_scan
    scan_complete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AttendanceRecord(Base):
    """
    Core attendance record. Status values from AttendanceStatus constants.
    IMPORTANT: Never delete records. Overrides add a new AuditLog row.
    """
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False, index=True)
    roll_number = Column(String, ForeignKey("users.roll_number"), nullable=False, index=True)
    status = Column(String, nullable=False)
    ai_confidence = Column(Float)          # Raw AI confidence score
    failure_code = Column(String)          # FailureCode if applicable
    used_upper_face = Column(Boolean, default=False)
    marked_at = Column(DateTime, default=datetime.utcnow)
    is_overridden = Column(Boolean, default=False)


class AttendanceAuditLog(Base):
    """
    US-04: Immutable audit log for every override.
    Append-only. No updates or deletes permitted.
    """
    __tablename__ = "attendance_audit_log"
    id = Column(Integer, primary_key=True)
    attendance_id = Column(Integer, ForeignKey("attendance_records.id"))
    session_id = Column(Integer, nullable=False)
    roll_number = Column(String, nullable=False)
    original_status = Column(String, nullable=False)
    original_ai_confidence = Column(Float)
    new_status = Column(String, nullable=False)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    faculty_name = Column(String)          # Denormalized for audit portability
    comment = Column(Text, nullable=False) # Mandatory per US-02 edge case !2
    override_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class EngagementRecord(Base):
    """
    Zone-level engagement aggregates per session.
    US-03: Never individual-level. Zone >= 8 students.
    Auto-deleted after HEATMAP_RETENTION_DAYS.
    """
    __tablename__ = "engagement_records"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False, index=True)
    zone_id = Column(String, nullable=False)       # e.g. 'R2C1'
    interval_start = Column(DateTime)
    interval_end = Column(DateTime)
    student_count = Column(Integer)                # US-03: must be >=8
    active_pct = Column(Float)
    passive_pct = Column(Float)
    disengaged_pct = Column(Float)
    is_merged_zone = Column(Boolean, default=False)  # True if <8 students merged
    insufficient_data = Column(Boolean, default=False)
    expires_at = Column(DateTime)                  # US-03: auto-delete after 30 days


class PhoneAlert(Base):
    __tablename__ = "phone_alerts"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("class_sessions.id"))
    zone_id = Column(String)
    confidence = Column(Float)
    detected_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_by_faculty = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)


class ContestRecord(Base):
    """US-05: Student can contest engagement classification within 24hrs."""
    __tablename__ = "contest_records"
    id = Column(Integer, primary_key=True)
    roll_number = Column(String, ForeignKey("users.roll_number"), nullable=False)
    session_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending | reviewed | resolved
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    resolution_comment = Column(Text, nullable=True)


class ExportLog(Base):
    """US-04: Every export is logged (who, when, which batch)."""
    __tablename__ = "export_logs"
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    batch_id = Column(String, nullable=False)
    format = Column(String, nullable=False)  # 'pdf' or 'excel'
    record_count = Column(Integer)
    exported_at = Column(DateTime, default=datetime.utcnow)
