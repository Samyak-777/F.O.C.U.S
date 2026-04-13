"""
Alert management for phone detections.
Handles deduplication and faculty notification.
"""
from datetime import datetime
from typing import List, Dict
from src.detection.phone_detector import PhoneDetection
from src.utils.logger import logger


class AlertManager:
    """Manages phone detection alerts — deduplicates and tracks acknowledgments."""

    def __init__(self):
        self.active_alerts: Dict[str, dict] = {}  # zone → alert info
        self.alert_history: List[dict] = []

    def process_detection(self, detection: PhoneDetection, session_id: str) -> dict | None:
        """
        Process a confirmed phone detection. Returns alert dict if new,
        None if already alerted for this zone recently.
        """
        zone = detection.zone or "unknown"

        # Deduplicate: don't re-alert for same zone within 60 seconds
        if zone in self.active_alerts:
            last_alert_time = self.active_alerts[zone].get("timestamp", 0)
            if (datetime.utcnow().timestamp() - last_alert_time) < 60:
                return None

        alert = {
            "session_id": session_id,
            "zone": zone,
            "confidence": detection.confidence,
            "timestamp": datetime.utcnow().timestamp(),
            "bbox": detection.bbox,
            "acknowledged": False
        }

        self.active_alerts[zone] = alert
        self.alert_history.append(alert)
        logger.warning(f"Phone alert: zone={zone} conf={detection.confidence:.2f}")

        return alert

    def acknowledge_alert(self, zone: str) -> bool:
        """Faculty acknowledges a phone alert."""
        if zone in self.active_alerts:
            self.active_alerts[zone]["acknowledged"] = True
            return True
        return False

    def get_active_alerts(self) -> List[dict]:
        """Get all unacknowledged alerts."""
        return [a for a in self.active_alerts.values() if not a["acknowledged"]]
