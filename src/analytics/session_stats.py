"""
Per-session statistics computation.
"""
from typing import Dict, List
from config.constants import AttendanceStatus


def compute_session_stats(attendance: Dict[str, str], total_enrolled: int) -> dict:
    """Compute summary statistics for a session."""
    present = sum(1 for s in attendance.values() if s == AttendanceStatus.PRESENT)
    late = sum(1 for s in attendance.values() if s == AttendanceStatus.LATE)
    unverified = sum(1 for s in attendance.values() if s == AttendanceStatus.UNVERIFIED)
    absent = total_enrolled - present - late - unverified

    return {
        "total_enrolled": total_enrolled,
        "present": present,
        "late": late,
        "unverified": unverified,
        "absent": absent,
        "attendance_rate": round((present + late) / max(total_enrolled, 1) * 100, 1)
    }
