"""
Push notifications for FOCUS system.
US-02: Attendance complete notification
US-03: Heatmap expiry reminder
US-06: Biometric deletion confirmation
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings
from src.utils.logger import logger


def send_email(to: str, subject: str, body: str):
    """Simple SMTP email sender."""
    try:
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning(f"SMTP not configured — email not sent: {subject}")
            return

        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {to}: {subject}")
    except Exception as e:
        logger.error(f"Email failed: {e}")


def notify_attendance_complete(faculty_email: str, present: int, total: int, session_id: str):
    """US-02: Push notification on scan completion."""
    send_email(
        to=faculty_email,
        subject=f"FOCUS — Attendance Complete: {present}/{total} present",
        body=(
            f"Attendance scan for session {session_id} is complete.\n"
            f"Present: {present}/{total}\n"
            f"View the dashboard to review Unverified entries.\n\n"
            f"— FOCUS System"
        )
    )


def notify_biometric_deletion(student_email: str, roll_number: str, deleted_at: str):
    """US-06: Deletion confirmation email after consent revocation."""
    send_email(
        to=student_email,
        subject="FOCUS — Your Biometric Data Has Been Deleted",
        body=(
            f"Dear {roll_number},\n\n"
            f"Your biometric data (facial embedding) has been permanently deleted "
            f"from the FOCUS system on {deleted_at} UTC.\n\n"
            f"Your attendance will now be marked via manual process.\n\n"
            f"— FOCUS System | VNIT Nagpur"
        )
    )


def notify_heatmap_expiry(faculty_email: str, session_date: str, expires_on: str):
    """US-03: 3-day advance reminder before heatmap auto-deletion."""
    send_email(
        to=faculty_email,
        subject="FOCUS — Engagement Heatmap Expiring in 3 Days",
        body=(
            f"The engagement heatmap for session on {session_date} will be "
            f"automatically deleted on {expires_on} (30-day retention policy).\n\n"
            f"Please download or review it before this date if needed.\n\n"
            f"— FOCUS System"
        )
    )
