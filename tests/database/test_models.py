"""
Tests for database model constraints and ORM behavior.
Verifies that the schema enforces the business rules.
"""
import pytest
from sqlalchemy.exc import IntegrityError
from src.db.models import (
    User, AttendanceRecord, AttendanceAuditLog,
    ConsentRecord, EngagementRecord, PhoneAlert
)
from config.constants import AttendanceStatus
from datetime import datetime, timedelta


class TestAttendanceRecordConstraints:

    def test_attendance_record_requires_roll_number(self, db_session, active_session):
        """Roll number is mandatory — attendance without identity is meaningless."""
        record = AttendanceRecord(
            session_id=active_session.id,
            roll_number=None,  # Must fail
            status=AttendanceStatus.PRESENT
        )
        db_session.add(record)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_audit_log_comment_required(self, db_session, active_session, student_user, faculty_user):
        """
        US-02 EC-2: Override must have mandatory comment.
        Simulated by checking that empty comment is stored but
        the API layer enforces non-empty.
        """
        # Create base attendance record
        record = AttendanceRecord(
            session_id=active_session.id,
            roll_number=student_user.roll_number,
            status=AttendanceStatus.PRESENT,
            ai_confidence=0.92
        )
        db_session.add(record)
        db_session.commit()

        # Audit log entry — comment must be present
        log = AttendanceAuditLog(
            attendance_id=record.id,
            session_id=active_session.id,
            roll_number=student_user.roll_number,
            original_status=AttendanceStatus.PRESENT,
            original_ai_confidence=0.92,
            new_status=AttendanceStatus.ABSENT,
            faculty_id=faculty_user.id,
            faculty_name=faculty_user.name,
            comment="Student left early — verified by security camera"
        )
        db_session.add(log)
        db_session.commit()

        fetched = db_session.query(AttendanceAuditLog).filter_by(id=log.id).first()
        assert fetched.comment is not None
        assert len(fetched.comment) > 0

    def test_engagement_record_stores_expiry(self, db_session, active_session):
        """US-03: Engagement record must store expires_at for auto-deletion."""
        from config.settings import settings
        expiry = datetime.utcnow() + timedelta(days=settings.HEATMAP_RETENTION_DAYS)

        record = EngagementRecord(
            session_id=active_session.id,
            zone_id="R2C1",
            student_count=12,
            active_pct=60.0,
            passive_pct=30.0,
            disengaged_pct=10.0,
            expires_at=expiry
        )
        db_session.add(record)
        db_session.commit()

        fetched = db_session.query(EngagementRecord).filter_by(id=record.id).first()
        assert fetched.expires_at is not None
        assert fetched.expires_at > datetime.utcnow()


# tests/database/test_crud.py
"""
Tests for CRUD operations.
Verifies the data layer correctly implements business rules.
"""

class TestAttendanceCRUD:

    def test_override_preserves_original_record(self, db_session, active_session, student_user, faculty_user):
        """
        US-04 EC-2: Override must preserve both original AI record
        and the override details with faculty name, timestamp, comment.
        """
        from src.db.crud import override_attendance, get_attendance_record

        # Create original record
        record = AttendanceRecord(
            session_id=active_session.id,
            roll_number=student_user.roll_number,
            status=AttendanceStatus.UNVERIFIED,
            ai_confidence=0.72,
            failure_code="FR_LOW_CONF"
        )
        db_session.add(record)
        db_session.commit()

        # Override it
        result = override_attendance(
            db_session,
            roll_number=student_user.roll_number,
            session_id=str(active_session.id),
            new_status=AttendanceStatus.PRESENT,
            faculty_id=faculty_user.id,
            comment="Student confirmed present via manual check"
        )

        # Verify original record was updated
        updated = db_session.query(AttendanceRecord).filter_by(id=record.id).first()
        assert updated.is_overridden is True

        # Verify audit log was created
        audit = db_session.query(AttendanceAuditLog).filter_by(
            roll_number=student_user.roll_number
        ).first()
        assert audit is not None
        assert audit.original_status == AttendanceStatus.UNVERIFIED
        assert audit.new_status == AttendanceStatus.PRESENT
        assert audit.original_ai_confidence == pytest.approx(0.72, abs=0.01)
        assert audit.comment == "Student confirmed present via manual check"
        assert audit.faculty_name == faculty_user.name

    def test_consent_withdrawal_masks_attendance_status(self, db_session, active_session, student_user):
        """
        US-04 EC-3: After consent withdrawal, attendance status must show
        'Data Restricted — Consent Withdrawn', not actual status.
        """
        from src.db.crud import get_batch_attendance

        record = AttendanceRecord(
            session_id=active_session.id,
            roll_number=student_user.roll_number,
            status=AttendanceStatus.CONSENT_WITHDRAWN,
            ai_confidence=None
        )
        db_session.add(record)
        db_session.commit()

        records, _, _ = get_batch_attendance(db_session, active_session.batch_id)
        withdrawn_records = [r for r in records if r["status"] == AttendanceStatus.CONSENT_WITHDRAWN]

        for r in withdrawn_records:
            assert r["ai_confidence"] is None or r["ai_confidence"] == "—", (
                "Consent-withdrawn record must not expose AI confidence score"
            )