# Attendance statuses — canonical values used across entire codebase
class AttendanceStatus:
    PRESENT = "Present"
    LATE = "Late"
    ABSENT = "Absent"
    UNVERIFIED = "Unverified"           # AI failed, needs manual review
    CAMERA_BLOCKED = "Camera_Blocked"   # Physical obstruction
    INCOMPLETE_SCAN = "Incomplete_Scan" # Camera dropped mid-session
    CONSENT_WITHDRAWN = "Data_Restricted_Consent_Withdrawn"


# Engagement states
class EngagementState:
    ACTIVE = "Active"
    PASSIVE = "Passive"
    DISENGAGED = "Disengaged"
    EYE_UNAVAILABLE = "Eye_Tracking_Unavailable"
    NOISY_SIGNAL = "Noisy_Signal_Inconclusive"
    SOCIAL_OCCLUSION = "Tracking_Interrupted_External_Obstruction"
    INSUFFICIENT_DATA = "Insufficient_Data"


# Failure codes for audit log
class FailureCode:
    LOW_CONFIDENCE = "FR_LOW_CONF"
    NO_FACE_DETECTED = "FR_NO_FACE"
    CAMERA_LOST = "FR_CAMERA_LOST"
    PHYSICAL_OBSTRUCTION = "FR_PHYS_BLOCKED"
    IR_GLARE = "ENG_IR_GLARE"
    DISTANCE_TOO_FAR = "FR_DISTANCE"
