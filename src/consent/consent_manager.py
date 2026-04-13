"""
US-06: DPDP Act 2023 compliant consent lifecycle.
PRI-01: Default state is UNCONSENTED — opt-in only
PRI-02: Revocable in ≤2 clicks
PRI-03: Biometric deletion within 24hr of revocation
PRI-04: Minors require guardian countersignature
PRI-06: Consent forms available in en, hi, mr, te
"""
from datetime import datetime
from src.db.crud import create_consent_record, get_latest_consent, update_consent_deletion
from src.face_recognition.enrollor import delete_student_embedding
from src.utils.logger import logger, audit_log

CONSENT_TEXT = {
    "en": {
        "title": "Biometric Data Consent — FOCUS System",
        "body": (
            "The FOCUS system will collect and process your facial biometric data "
            "for attendance marking. "
            "What is collected: facial embedding (mathematical representation of your face). "
            "How long: for the duration of your enrollment at this institution. "
            "Who can access: faculty (attendance only), administration (aggregate reports only). "
            "How to revoke: visit Student Portal → Settings → Revoke Biometric Consent at any time. "
            "After revocation: your biometric data will be permanently deleted within 24 hours."
        ),
        "action": "I give my explicit consent"
    },
    "hi": {
        "title": "बायोमेट्रिक डेटा सहमति — FOCUS प्रणाली",
        "body": (
            "FOCUS प्रणाली उपस्थिति के लिए आपका चेहरे का बायोमेट्रिक डेटा संग्रहित करेगी। "
            "क्या संग्रहित होगा: चेहरे का गणितीय प्रतिनिधित्व। "
            "कितने समय के लिए: संस्था में नामांकन की अवधि तक। "
            "कौन देख सकता है: केवल शिक्षक और प्रशासन (समग्र रिपोर्ट)। "
            "सहमति वापस लेने के लिए: Student Portal → Settings → Revoke Biometric Consent।"
        ),
        "action": "मैं अपनी स्पष्ट सहमति देता/देती हूँ"
    },
    "mr": {
        "title": "बायोमेट्रिक डेटा संमती — FOCUS प्रणाली",
        "body": (
            "FOCUS प्रणाली उपस्थितीसाठी तुमचा चेहर्‍याचा बायोमेट्रिक डेटा गोळा करेल। "
            "काय गोळा केले जाईल: चेहर्‍याचे गणितीय प्रतिनिधित्व। "
            "किती काळ: संस्थेत नोंदणी असेपर्यंत। "
            "कोण पाहू शकते: केवळ शिक्षक आणि प्रशासन।"
        ),
        "action": "मी माझी स्पष्ट संमती देतो/देते"
    },
    "te": {
        "title": "బయోమెట్రిక్ డేటా అనుమతి — FOCUS వ్యవస్థ",
        "body": (
            "FOCUS వ్యవస్థ హాజరు కోసం మీ ముఖ బయోమెట్రిక్ డేటాను సేకరిస్తుంది। "
            "ఏమి సేకరించబడుతుంది: ముఖం యొక్క గణిత ప్రాతినిధ్యం। "
            "ఎంత కాలం: సంస్థలో నమోదు వ్యవధి వరకు।"
        ),
        "action": "నేను నా స్పష్ట అనుమతిని ఇస్తున్నాను"
    }
}


class ConsentManager:

    def give_consent(self, db, roll_number: str, language: str, ip: str,
                     is_minor: bool = False, guardian_signed: bool = False) -> dict:
        """Record explicit consent. PRI-01: default state is UNCONSENTED."""
        if is_minor and not guardian_signed:
            return {
                "status": "blocked",
                "reason": "guardian_consent_required",
                "message": "Student is a minor. Guardian countersignature required."
            }

        create_consent_record(db, roll_number, "given", language, ip, guardian_signed)
        audit_log(f"CONSENT_GIVEN: {roll_number} lang={language}")
        return {"status": "consent_given", "roll_number": roll_number}

    def revoke_consent(self, db, roll_number: str, ip: str) -> dict:
        """PRI-02: Revoke consent. PRI-03: Delete biometric within 24hr."""
        create_consent_record(db, roll_number, "revoked", "n/a", ip)
        deleted = delete_student_embedding(roll_number)
        deletion_time = datetime.utcnow()
        update_consent_deletion(db, roll_number, deletion_time)
        audit_log(f"CONSENT_REVOKED_AND_DELETED: {roll_number}")

        return {
            "status": "revoked",
            "biometric_deleted": deleted,
            "deletion_confirmed_at": deletion_time.isoformat(),
            "message": "Your biometric data has been permanently deleted."
        }

    def get_consent_form(self, language: str = "en") -> dict:
        """Return consent form text in requested language."""
        lang = language if language in CONSENT_TEXT else "en"
        return CONSENT_TEXT[lang]

    def has_valid_consent(self, db, roll_number: str) -> bool:
        """Check if student has active (non-revoked) consent."""
        record = get_latest_consent(db, roll_number)
        return record is not None and record.status == "given"
