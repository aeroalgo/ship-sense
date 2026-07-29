from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from collector.plugins.mqtt.payloads import (
    AnalogChannelPayload,
    DiscreteChannelPayload,
    ExhaustGasGroupPayload,
    LogicalEventPayload,
    PayloadUnion,
)

_KIND_MODELS: dict[str, type[PayloadUnion]] = {
    "analog": AnalogChannelPayload,
    "discrete": DiscreteChannelPayload,
    "event": LogicalEventPayload,
    "egt": ExhaustGasGroupPayload,
}


class MqttParseError(ValueError):
    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"{path}: {reason}")


def parse_mqtt_payload(topic: str, data: dict[str, Any] | bytes) -> PayloadUnion:
    expected_kind, topic_channel = _parse_topic(topic)
    payload_data = _decode_payload(data)
    if "@type" in payload_data and payload_data["@type"] != expected_kind:
        raise MqttParseError("@type", "type_topic_mismatch")
    model = _KIND_MODELS[expected_kind]

    try:
        payload = model.model_validate_json(json.dumps(payload_data))
    except ValidationError as exc:
        error = exc.errors()[0]
        location = ".".join(str(part) for part in error["loc"]) or "$"
        reason = _validation_reason(error)
        raise MqttParseError(location, reason) from exc

    if payload.channel_id != topic_channel:
        raise MqttParseError("channel_id", "channel_mismatch")
    if payload.message_type != expected_kind:
        raise MqttParseError("@type", "type_topic_mismatch")
    return payload


def _parse_topic(topic: str) -> tuple[str, str]:
    parts = topic.split("/")
    if len(parts) != 5 or parts[0] != "shipsense":
        raise MqttParseError("topic", "invalid_topic")
    _, version, _panel, kind, channel_id = parts
    if version != "v1":
        raise MqttParseError("topic.version", "unsupported_version")
    if kind not in _KIND_MODELS:
        raise MqttParseError("topic.kind", "unknown_kind")
    if not channel_id:
        raise MqttParseError("topic.channel_id", "missing_channel_id")
    return kind, channel_id


def _decode_payload(data: dict[str, Any] | bytes) -> dict[str, Any]:
    if isinstance(data, bytes):
        try:
            decoded = json.loads(data)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MqttParseError("payload", "invalid_json") from exc
    else:
        decoded = data
    if not isinstance(decoded, dict):
        raise MqttParseError("payload", "object_required")
    return decoded


def _validation_reason(error: dict[str, Any]) -> str:
    error_type = str(error.get("type", "validation_error"))
    if error_type in {"enum", "literal_error"}:
        return "invalid_enum"
    if error_type == "missing":
        return "required"
    if error_type == "extra_forbidden":
        return "unknown_field"
    if error_type == "value_error" and "unsupported_version" in str(error.get("msg")):
        return "unsupported_version"
    return error_type


__all__ = [
    "AnalogChannelPayload",
    "DiscreteChannelPayload",
    "ExhaustGasGroupPayload",
    "LogicalEventPayload",
    "MqttParseError",
    "PayloadUnion",
    "parse_mqtt_payload",
]
