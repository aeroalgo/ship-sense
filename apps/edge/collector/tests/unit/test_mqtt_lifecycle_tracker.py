from datetime import datetime, timezone

import pytest

from collector.domain.models import EventSeverity, Quality
from collector.plugins.mqtt.lifecycle_tracker import MqttLifecycleTracker
from collector.plugins.mqtt.payloads import DiscreteApsState

UTC_NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


def test_first_observation_is_silent_and_transition_emits_event() -> None:
    tracker = MqttLifecycleTracker(source_id="aps_main")

    assert tracker.observe("APS.TAI4101", "normal", UTC_NOW, "analog") is None

    event = tracker.observe(
        "APS.TAI4101", "exceeded_unacked", UTC_NOW, "analog"
    )

    assert event is not None
    assert event.event_name == "aps.threshold.exceeded"
    assert event.params == {
        "lifecycle": "active",
        "kanoner_state": "exceeded_unacked",
        "reconstructed": False,
    }
    assert event.source == "aps_main"
    assert event.tag_id == "APS.TAI4101"
    assert event.severity is EventSeverity.ALARM
    assert event.idempotency_key == (
        "aps_main:APS.TAI4101:active:2026-07-28T12:00:00+00:00"
    )


def test_repeated_state_does_not_emit_duplicate_event() -> None:
    tracker = MqttLifecycleTracker(source_id="aps_main")

    tracker.observe("GEU.DI2201", "normal", UTC_NOW, "discrete")
    first = tracker.observe(
        "GEU.DI2201", "active_unacked", UTC_NOW, "discrete"
    )
    repeat = tracker.observe(
        "GEU.DI2201", "active_unacked", UTC_NOW, "discrete"
    )

    assert first is not None
    assert repeat is None


def test_returned_unacked_and_blocked_keep_distinct_lifecycle_values() -> None:
    tracker = MqttLifecycleTracker(source_id="aps_main")
    tracker.observe("APS.TAI4101", "normal", UTC_NOW, "analog")

    returned = tracker.observe(
        "APS.TAI4101", "returned_unacked", UTC_NOW, "analog"
    )
    blocked = tracker.observe("APS.TAI4101", "blocked", UTC_NOW, "analog")

    assert returned is not None
    assert returned.params["lifecycle"] == "returned_unacked"
    assert returned.event_name == "aps.threshold.returned_unacked"
    assert blocked is not None
    assert blocked.params["lifecycle"] == "suppressed"
    assert blocked.params["kanoner_state"] == "blocked"
    assert blocked.event_name == "aps.threshold.blocked"


def test_same_transition_and_timestamp_is_idempotent() -> None:
    tracker = MqttLifecycleTracker(source_id="aps_main")

    tracker.observe("APS.EV0101", "disabled", UTC_NOW, "event")
    first = tracker.observe("APS.EV0101", "enabled", UTC_NOW, "event")
    tracker.observe("APS.EV0101", "disabled", UTC_NOW, "event")
    duplicate = tracker.observe("APS.EV0101", "enabled", UTC_NOW, "event")

    assert first is not None
    assert duplicate is None


def test_logical_event_mapping_emits_native_event_name() -> None:
    tracker = MqttLifecycleTracker(source_id="aps_main")
    tracker.observe("APS.EV0101", "disabled", UTC_NOW, "event")

    event = tracker.observe("APS.EV0101", "enabled", UTC_NOW, "event")

    assert event is not None
    assert event.event_name == "aps.event.enabled"
    assert event.params["lifecycle"] == "active"
    assert event.severity is EventSeverity.INFO


def test_test_mode_event_is_uncertain_and_not_suppressed() -> None:
    tracker = MqttLifecycleTracker(source_id="aps_main")
    tracker.observe("APS.EV0101", "disabled", UTC_NOW, "event")

    event = tracker.observe(
        "APS.EV0101", "enabled", UTC_NOW, "event", channel_test_enabled=True
    )

    assert event is not None
    assert event.quality is Quality.UNCERTAIN
    assert event.params["test_mode"] is True
    assert event.params["reconstructed"] is False


def test_state_enum_must_match_lifecycle_kind() -> None:
    tracker = MqttLifecycleTracker(source_id="aps_main")

    with pytest.raises(ValueError, match="unsupported MQTT lifecycle state"):
        tracker.observe(
            "APS.TAI4101",
            DiscreteApsState.NORMAL,
            UTC_NOW,
            "analog",
        )
