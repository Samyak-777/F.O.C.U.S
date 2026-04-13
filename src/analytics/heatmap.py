"""
US-03: Zone-wise engagement heatmap.
HM-01: Minimum 8 students per zone (merge if fewer)
HM-02: Faculty-only visibility
HM-03: Auto-delete after 30 days
HM-04: 0% engagement → flag as Anomaly
"""
from datetime import datetime, timedelta
from config.settings import settings
from config.constants import EngagementState


def generate_heatmap(session_id: str, summaries: dict) -> dict:
    """
    Generate zone-level heatmap from per-tracker engagement summaries.
    summaries: { tracker_key: { state, active_pct, passive_pct, disengaged_pct, samples } }
    """
    zone_data: dict = {}

    for tracker_key, summary in summaries.items():
        zone_id = tracker_key.split("_")[0] if tracker_key.startswith("R") else "R1C1"

        if zone_id not in zone_data:
            zone_data[zone_id] = {
                "students": [],
                "active_sum": 0.0,
                "passive_sum": 0.0,
                "disengaged_sum": 0.0
            }

        if summary.get("state") != EngagementState.INSUFFICIENT_DATA:
            zone_data[zone_id]["students"].append(tracker_key)
            zone_data[zone_id]["active_sum"] += summary.get("active_pct", 0)
            zone_data[zone_id]["passive_sum"] += summary.get("passive_pct", 0)
            zone_data[zone_id]["disengaged_sum"] += summary.get("disengaged_pct", 0)

    output_zones = {}

    for zone_id, data in zone_data.items():
        n = len(data["students"])

        if n < settings.ZONE_MIN_STUDENTS:
            output_zones[zone_id] = {
                "student_count": n,
                "insufficient_data": True,
                "state": EngagementState.INSUFFICIENT_DATA,
                "note": f"Only {n} students — below minimum of {settings.ZONE_MIN_STUDENTS}"
            }
            continue

        active_pct = data["active_sum"] / n
        passive_pct = data["passive_sum"] / n
        disengaged_pct = data["disengaged_sum"] / n

        if active_pct >= passive_pct and active_pct >= disengaged_pct:
            dominant = EngagementState.ACTIVE
        elif passive_pct >= disengaged_pct:
            dominant = EngagementState.PASSIVE
        else:
            dominant = EngagementState.DISENGAGED

        # HM-04: 0% engagement → Anomaly flag
        is_anomaly = (active_pct == 0 and passive_pct == 0 and disengaged_pct == 0)

        output_zones[zone_id] = {
            "student_count": n,
            "state": dominant,
            "active_pct": round(active_pct, 1),
            "passive_pct": round(passive_pct, 1),
            "disengaged_pct": round(disengaged_pct, 1),
            "insufficient_data": False,
            "is_anomaly": is_anomaly,
            "anomaly_message": "Anomaly — Please Verify" if is_anomaly else None,
            "expires_at": (datetime.utcnow() + timedelta(days=settings.HEATMAP_RETENTION_DAYS)).isoformat()
        }

    return {
        "session_id": session_id,
        "generated_at": datetime.utcnow().isoformat(),
        "zones": output_zones,
        "note": "Heatmap accessible to faculty only. Zone minimum: 8 students."
    }
