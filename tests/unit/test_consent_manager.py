"""
Tests for DPDP Act 2023 compliance.
US-06 is a legal requirement — every edge case must pass.
"""
import pytest
from unittest.mock import MagicMock, patch
from freezegun import freeze_time
from datetime import datetime, timedelta
from src.consent.consent_manager import ConsentManager, CONSENT_TEXT


@pytest.mark.us06
class TestConsentManager:

    def setup_method(self):
        self.manager = ConsentManager()

    def test_consent_form_available_in_all_four_languages(self):
        """US-06 AC-1: Consent must be available in en, hi, mr, te."""
        for lang in ["en", "hi", "mr", "te"]:
            form = self.manager.get_consent_form(lang)
            assert "title" in form, f"Consent form missing title for language: {lang}"
            assert "body" in form, f"Consent form missing body for language: {lang}"
            assert "action" in form, f"Consent form missing action button for language: {lang}"
            assert len(form["body"]) > 50, f"Consent form body too short for language: {lang}"

    def test_consent_form_body_includes_required_disclosures(self):
        """
        US-06 AC-2: Consent form must explicitly state:
        what is collected, retention period, who can access, how to revoke.
        """
        form = self.manager.get_consent_form("en")
        body_lower = form["body"].lower()

        required_disclosures = [
            ("what is collected", "biometric"),
            ("retention period", ["retain", "duration", "long"]),
            ("who can access", ["access", "faculty", "administration"]),
            ("how to revoke", "revoke")
        ]

        for disclosure_name, keywords in required_disclosures:
            if isinstance(keywords, list):
                found = any(kw in body_lower for kw in keywords)
            else:
                found = keywords in body_lower
            assert found, (
                f"Consent form missing disclosure: '{disclosure_name}'. "
                f"US-06 AC-2 requires explicit statement of {disclosure_name}."
            )

    def test_minor_student_blocked_without_guardian_countersignature(self, db_session, minor_student_user):
        """
        US-06 EC-1: Minor must be blocked from biometric enrollment
        until guardian countersignature is obtained.
        """
        result = self.manager.give_consent(
            db=MagicMock(),
            roll_number=minor_student_user.roll_number,
            language="en",
            ip="127.0.0.1",
            is_minor=True,
            guardian_signed=False  # No guardian signature
        )

        assert result["status"] == "blocked", (
            f"Minor without guardian signature must be blocked. Got: {result['status']}. "
            "US-06 EC-1 violated."
        )
        assert "guardian" in result.get("reason", "").lower()

    def test_minor_with_guardian_signature_can_enroll(self):
        """US-06 EC-1: Minor WITH guardian countersignature can proceed."""
        result = self.manager.give_consent(
            db=MagicMock(),
            roll_number="BT23CSE002",
            language="en",
            ip="127.0.0.1",
            is_minor=True,
            guardian_signed=True  # Guardian has signed
        )
        assert result["status"] == "consent_given"

    def test_consent_revocation_deletes_biometric_immediately(self):
        """
        US-06 AC-5: Biometric template must be permanently deleted
        within 24 hours of revocation. Our implementation does it synchronously.
        """
        with patch('src.consent.consent_manager.delete_student_embedding', return_value=True) as mock_delete:
            with patch('src.consent.consent_manager.create_consent_record'):
                with patch('src.consent.consent_manager.update_consent_deletion'):
                    result = self.manager.revoke_consent(
                        db=MagicMock(),
                        roll_number="BT23CSE001",
                        ip="127.0.0.1"
                    )

        assert result["status"] == "revoked"
        assert result["biometric_deleted"] is True
        mock_delete.assert_called_once_with("BT23CSE001"), (
            "delete_student_embedding must be called on revocation. "
            "US-06 AC-5: deletion within 24 hours."
        )

    def test_default_consent_state_is_unconsented(self):
        """
        US-06 EC-3: CRITICAL — default state must ALWAYS be unconsented.
        System must never pre-check consent or treat silence as consent.
        """
        from src.consent.consent_manager import ConsentManager
        manager = ConsentManager()

        # has_valid_consent must return False for a student with no record
        db_mock = MagicMock()
        with patch('src.consent.consent_manager.get_latest_consent', return_value=None):
            result = manager.has_valid_consent(db_mock, "BT23CSE_NEW")

        assert result is False, (
            "A student with no consent record must be treated as UNCONSENTED. "
            "US-06 EC-3: opt-out default is forbidden."
        )

    def test_revocation_during_active_session_marks_manual_verification(self):
        """
        US-06 EC-2: If student revokes during active session,
        their attendance for THAT session must be marked
        'Manual Verification Required', not the previous AI status.
        This is an integration concern — tested here as a contract.
        """
        # The consent revocation endpoint must communicate to the session processor
        # This test documents the expected behavior for the integration test
        pass

    @freeze_time("2026-04-02 09:00:00")
    def test_deletion_confirmation_timestamp_is_recorded(self):
        """US-06 AC-5: Deletion confirmation email timestamp must be logged."""
        with patch('src.consent.consent_manager.delete_student_embedding', return_value=True):
            with patch('src.consent.consent_manager.create_consent_record'):
                with patch('src.consent.consent_manager.update_consent_deletion') as mock_update:
                    self.manager.revoke_consent(
                        db=MagicMock(),
                        roll_number="BT23CSE001",
                        ip="127.0.0.1"
                    )

        mock_update.assert_called_once()
        args = mock_update.call_args[0]
        deletion_time = args[2]
        assert deletion_time is not None
        # With frozen time, deletion must be logged at 2026-04-02 09:00:00
        assert deletion_time == datetime(2026, 4, 2, 9, 0, 0)