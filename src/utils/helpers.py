"""
General utility helpers for FOCUS.
"""
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hex digest for document signing (EXP-02)."""
    return hashlib.sha256(data).hexdigest()


def is_within_window(start_time: datetime, window_minutes: int) -> bool:
    """Check if current time is within a time window from start."""
    return datetime.utcnow() <= start_time + timedelta(minutes=window_minutes)


def format_confidence(confidence: float) -> str:
    """Format confidence as percentage string."""
    return f"{confidence * 100:.1f}%"


def truncate_string(s: str, max_length: int = 40) -> str:
    """Truncate a string with ellipsis if too long."""
    if len(s) > max_length:
        return s[:max_length - 3] + "..."
    return s
