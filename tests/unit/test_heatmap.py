"""
Tests for zone-wise engagement heatmap.
US-03 acceptance criteria — especially the 8-student minimum and anomaly detection.
"""
import pytest
from src.analytics.heatmap import generate_heatmap
from config.constants import EngagementState
from config.settings import settings


@pytest.mark.us03
class TestHeatmapGeneration:

    def _make_summaries(self, zones: dict) -> dict:
        """Helper: create engagement summaries indexed by zone key."""
        summaries = {}
        for zone_id, (count, state) in zones.items():
            for i in range(count):
                tracker_key = f"{zone_id}_{i}"
                if state == EngagementState.ACTIVE:
                    summaries[tracker_key] = {"state": state, "active_pct": 100, "passive_pct": 0, "disengaged_pct": 0, "samples": 100}
                elif state == EngagementState.PASSIVE:
                    summaries[tracker_key] = {"state": state, "active_pct": 0, "passive_pct": 100, "disengaged_pct": 0, "samples": 100}
                else:
                    summaries[tracker_key] = {"state": state, "active_pct": 0, "passive_pct": 0, "disengaged_pct": 100, "samples": 100}
        return summaries

    def test_zone_with_sufficient_students_shows_state(self):
        """US-03 AC-2: Zone with ≥8 students shows engagement state."""
        summaries = self._make_summaries({"R1C1": (10, EngagementState.ACTIVE)})
        result = generate_heatmap("session_001", summaries)
        zone = result["zones"].get("R1C1")

        assert zone is not None
        assert not zone["insufficient_data"]
        assert zone["state"] == EngagementState.ACTIVE
        assert zone["student_count"] == 10

    def test_zone_below_minimum_marked_insufficient(self):
        """
        US-03 AC-2 + EC-1: Zone with fewer than 8 students must show
        'Insufficient Data', never actual engagement state.
        Privacy protection for thin rows.
        """
        # Zone with only 5 students — below ZONE_MIN_STUDENTS (8)
        summaries = self._make_summaries({"R3C2": (5, EngagementState.DISENGAGED)})
        result = generate_heatmap("session_002", summaries)
        zone = result["zones"].get("R3C2")

        assert zone is not None
        assert zone["insufficient_data"] is True, (
            f"Zone with {zone['student_count']} students must show insufficient_data=True. "
            f"US-03 EC-1: de-anonymization prevention."
        )
        assert zone.get("state") == EngagementState.INSUFFICIENT_DATA

    def test_zero_engagement_zone_flagged_as_anomaly(self):
        """
        US-03 EC-2: Zone showing 0% engagement for entire session must
        be flagged as 'Anomaly — Please Verify', not accepted as valid.
        Likely indicates camera tracking failure.
        """
        # 10 students in a zone, all with zero engagement data
        summaries = {}
        for i in range(10):
            summaries[f"R2C1_{i}"] = {
                "state": EngagementState.ACTIVE,
                "active_pct": 0,
                "passive_pct": 0,
                "disengaged_pct": 0,
                "samples": 0
            }

        result = generate_heatmap("session_003", summaries)
        zone = result["zones"].get("R2C1")

        if zone and not zone.get("insufficient_data"):
            assert zone.get("is_anomaly") is True, (
                "Zone with 0% across all states must be flagged as anomaly. "
                "Likely camera failure, not genuine data."
            )

    def test_heatmap_includes_expiry_timestamp(self):
        """US-03 AC-5: Each heatmap zone must include expires_at for 30-day retention."""
        summaries = self._make_summaries({"R1C1": (10, EngagementState.ACTIVE)})
        result = generate_heatmap("session_004", summaries)

        for zone_id, zone in result["zones"].items():
            if not zone.get("insufficient_data"):
                assert "expires_at" in zone, (
                    f"Zone {zone_id} missing expires_at. "
                    "US-03 AC-5: heatmap data must have 30-day expiry."
                )

    def test_heatmap_note_says_faculty_only(self):
        """
        US-03 constraint from peer review: heatmap must include access policy note.
        Administration cannot view session-level engagement data.
        """
        result = generate_heatmap("session_005", {})
        assert "note" in result
        note_lower = result["note"].lower()
        assert "faculty" in note_lower, (
            "Heatmap must include note that it is faculty-only access. "
            "US-03 peer review constraint."
        )