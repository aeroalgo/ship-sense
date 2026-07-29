from datetime import datetime, timezone
from types import SimpleNamespace

from collector.plugins.mqtt.lifecycle_tracker import MqttLifecycleTracker
from collector.plugins.mqtt.mapper import MqttSemanticMapper
from collector.plugins.mqtt.parser import parse_mqtt_payload

UTC_NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


def _payload(name: str, topic: str):
    import json
    from pathlib import Path

    data = json.loads(
        (Path(__file__).parents[1] / "fixtures" / "mqtt" / name).read_text()
    )
    return parse_mqtt_payload(topic, data)


def _mapper(entries: dict[str, object]) -> MqttSemanticMapper:
    return MqttSemanticMapper(
        lifecycle_tracker=MqttLifecycleTracker(source_id="panel_aps"),
        channel_map=entries,
    )


def test_analog_maps_value_and_threshold_pseudo_tags() -> None:
    mapper = _mapper(
        {
            "APS.TAI4101": SimpleNamespace(
                tag_id="TAI4101",
                kind="analog",
                unit="degC",
                thresholds=SimpleNamespace(expose=True),
            )
        }
    )
    payload = _payload("analog.json", "shipsense/v1/aps/analog/APS.TAI4101")

    result = mapper.map("panel_aps", payload, UTC_NOW)

    assert [sample.native_id for sample in result.samples] == [
        "APS.TAI4101",
        "APS.TAI4101#VVU",
        "APS.TAI4101#VU",
        "APS.TAI4101#NU",
        "APS.TAI4101#NNU",
    ]
    assert [sample.raw_value for sample in result.samples] == [
        82.5,
        90.0,
        85.0,
        15.0,
        10.0,
    ]
    assert all(
        sample.source_ts == payload.source_ts for sample in result.samples
    )
    assert result.event is None


def test_analog_thresholds_can_be_disabled() -> None:
    mapper = _mapper(
        {
            "APS.TAI4101": {
                "tag_id": "TAI4101",
                "kind": "analog",
                "thresholds": {"expose": False},
            }
        }
    )
    payload = _payload("analog.json", "shipsense/v1/aps/analog/APS.TAI4101")

    result = mapper.map("panel_aps", payload, UTC_NOW)

    assert len(result.samples) == 1
    assert result.samples[0].raw_value == 82.5


def test_lifecycle_transition_is_returned_with_samples() -> None:
    mapper = _mapper(
        {"APS.TAI4101": {"tag_id": "TAI4101", "kind": "analog"}}
    )
    first = _payload("analog.json", "shipsense/v1/aps/analog/APS.TAI4101")
    second = first.model_copy(update={"aps_state": "exceeded_unacked"})

    assert mapper.map("panel_aps", first, UTC_NOW).event is None
    result = mapper.map("panel_aps", second, UTC_NOW)

    assert result.event is not None
    assert result.event.event_name == "aps.threshold.exceeded"
    assert result.event.params["reconstructed"] is False


def test_egt_expands_cylinder_deviations() -> None:
    mapper = _mapper(
        {"GEU.EGT1": {"tag_id": "GEU.EGT1", "kind": "egt_group"}}
    )
    payload = _payload("egt.json", "shipsense/v1/geu/egt/GEU.EGT1")

    result = mapper.map("panel_aps", payload, UTC_NOW)

    assert len(result.samples) == 12
    assert result.samples[0].native_id == "GEU.EGT1#CYL1.DEV"
    assert result.samples[0].raw_value == 1.0
    assert result.samples[-1].native_id == "GEU.EGT1#CYL12.DEV"
    assert result.samples[-1].raw_value == 12.0
    assert all("#CYL" in sample.native_id for sample in result.samples)
    assert all(sample.source_ts == payload.source_ts for sample in result.samples)


def test_unknown_channel_is_quarantined_instead_of_dropped() -> None:
    mapper = _mapper({})
    payload = _payload("analog.json", "shipsense/v1/aps/analog/APS.TAI4101")

    result = mapper.map("panel_aps", payload, UTC_NOW)

    assert len(result.samples) == 1
    assert result.samples[0].native_id == "APS.TAI4101"
    assert result.samples[0].native_quality == "mqtt.quarantine.unknown_channel"
    assert result.quarantine_reason == "unknown_channel"
