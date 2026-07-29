from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from collector.plugins.mqtt.parser import (
    AnalogChannelPayload,
    DiscreteChannelPayload,
    ExhaustGasGroupPayload,
    LogicalEventPayload,
    MqttParseError,
    parse_mqtt_payload,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "mqtt"


@pytest.mark.parametrize(
    ("fixture", "topic", "expected_type"),
    [
        ("analog.json", "shipsense/v1/aps/analog/APS.TAI4101", AnalogChannelPayload),
        ("discrete.json", "shipsense/v1/geu/discrete/GEU.DI2201", DiscreteChannelPayload),
        ("event.json", "shipsense/v1/aps/event/APS.EV0101", LogicalEventPayload),
        ("egt.json", "shipsense/v1/geu/egt/GEU.EGT1", ExhaustGasGroupPayload),
    ],
)
def test_golden_payloads_parse_to_typed_models(
    fixture: str, topic: str, expected_type: type[Any]
) -> None:
    data = json.loads((FIXTURES / fixture).read_text())

    payload = parse_mqtt_payload(topic, data)

    assert isinstance(payload, expected_type)
    assert payload.schema_version == "1.0"
    assert payload.channel_id == topic.rsplit("/", 1)[-1]


def test_bytes_json_payload_is_supported() -> None:
    topic = "shipsense/v1/aps/analog/APS.TAI4101"
    data = (FIXTURES / "analog.json").read_bytes()

    payload = parse_mqtt_payload(topic, data)

    assert isinstance(payload, AnalogChannelPayload)
    assert payload.value == 82.5


def test_invalid_enum_reports_field_path() -> None:
    data = json.loads((FIXTURES / "analog.json").read_text())
    data["aps_state"] = "not-a-state"

    with pytest.raises(MqttParseError, match=r"aps_state"):
        parse_mqtt_payload("shipsense/v1/aps/analog/APS.TAI4101", data)


def test_missing_required_field_reports_field_path() -> None:
    data = json.loads((FIXTURES / "discrete.json").read_text())
    del data["input_active"]

    with pytest.raises(MqttParseError, match=r"input_active"):
        parse_mqtt_payload("shipsense/v1/geu/discrete/GEU.DI2201", data)


def test_topic_and_payload_type_must_match() -> None:
    data = json.loads((FIXTURES / "analog.json").read_text())
    data["@type"] = "discrete"

    with pytest.raises(MqttParseError, match="type_topic_mismatch"):
        parse_mqtt_payload("shipsense/v1/aps/analog/APS.TAI4101", data)


def test_unknown_topic_kind_is_explicit_error() -> None:
    data = json.loads((FIXTURES / "analog.json").read_text())

    with pytest.raises(MqttParseError, match="unknown_kind"):
        parse_mqtt_payload("shipsense/v1/aps/unknown/APS.TAI4101", data)


def test_channel_mismatch_is_explicit_error() -> None:
    data = json.loads((FIXTURES / "analog.json").read_text())
    data["channel_id"] = "APS.OTHER"

    with pytest.raises(MqttParseError, match="channel_mismatch"):
        parse_mqtt_payload("shipsense/v1/aps/analog/APS.TAI4101", data)


def test_malformed_json_is_typed_error() -> None:
    with pytest.raises(MqttParseError, match="invalid_json"):
        parse_mqtt_payload(
            "shipsense/v1/aps/analog/APS.TAI4101", b"{not-json"
        )
