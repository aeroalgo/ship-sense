from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from app.events.models import Event, EventSeverity
from app.telemetry.models import Quality
from collector.plugins.mqtt.payloads import (
    AnalogApsState,
    DiscreteApsState,
    LogicalEventState,
)


LifecycleKey = tuple[str, str]


_ANALOG_MAPPING: dict[AnalogApsState, tuple[str, str, EventSeverity]] = {
    AnalogApsState.NORMAL: (
        "cleared",
        "aps.threshold.cleared",
        EventSeverity.INFO,
    ),
    AnalogApsState.EXCEEDED_UNACKED: (
        "active",
        "aps.threshold.exceeded",
        EventSeverity.ALARM,
    ),
    AnalogApsState.RETURNED_UNACKED: (
        "returned_unacked",
        "aps.threshold.returned_unacked",
        EventSeverity.WARNING,
    ),
    AnalogApsState.EXCEEDED_ACKED: (
        "active_acked",
        "aps.threshold.exceeded_acked",
        EventSeverity.WARNING,
    ),
    AnalogApsState.BLOCKED: (
        "suppressed",
        "aps.threshold.blocked",
        EventSeverity.INFO,
    ),
}

_DISCRETE_MAPPING: dict[DiscreteApsState, tuple[str, str, EventSeverity]] = {
    DiscreteApsState.NORMAL: (
        "cleared",
        "aps.discrete.cleared",
        EventSeverity.INFO,
    ),
    DiscreteApsState.ACTIVE_UNACKED: (
        "active",
        "aps.discrete.active",
        EventSeverity.ALARM,
    ),
    DiscreteApsState.PASSIVE_UNACKED: (
        "returned_unacked",
        "aps.discrete.passive_unacked",
        EventSeverity.WARNING,
    ),
    DiscreteApsState.ACTIVE_ACKED: (
        "active_acked",
        "aps.discrete.active_acked",
        EventSeverity.WARNING,
    ),
    DiscreteApsState.BLOCKED: (
        "suppressed",
        "aps.discrete.blocked",
        EventSeverity.INFO,
    ),
}

_EVENT_MAPPING: dict[LogicalEventState, tuple[str, str, EventSeverity]] = {
    LogicalEventState.DISABLED: (
        "cleared",
        "aps.event.disabled",
        EventSeverity.INFO,
    ),
    LogicalEventState.ENABLED: (
        "active",
        "aps.event.enabled",
        EventSeverity.INFO,
    ),
    LogicalEventState.BLOCKED: (
        "suppressed",
        "aps.event.blocked",
        EventSeverity.INFO,
    ),
}

_MAPPINGS: dict[str, dict[Any, tuple[str, str, EventSeverity]]] = {
    "analog": _ANALOG_MAPPING,
    "discrete": _DISCRETE_MAPPING,
    "event": _EVENT_MAPPING,
}


class MqttLifecycleTracker:
    """Emit one native MQTT event when a channel lifecycle changes."""

    def __init__(self, source_id: str) -> None:
        self.source_id = source_id
        self._previous: dict[LifecycleKey, Any] = {}
        self._emitted_keys: set[str] = set()

    def observe(
        self,
        channel_id: str,
        aps_state: Any,
        source_ts: datetime,
        kind: str,
        *,
        channel_test_enabled: bool = False,
    ) -> Event | None:
        mapping = _MAPPINGS.get(kind)
        if mapping is None:
            raise ValueError(f"unsupported MQTT lifecycle kind: {kind}")

        state = self._coerce_state(mapping, aps_state)
        key = (self.source_id, channel_id)
        previous = self._previous.get(key)
        self._previous[key] = state
        if previous is None or previous == state:
            return None

        lifecycle, event_name, severity = mapping[state]
        idempotency_key = ":".join(
            (self.source_id, channel_id, lifecycle, source_ts.isoformat())
        )
        if idempotency_key in self._emitted_keys:
            return None
        self._emitted_keys.add(idempotency_key)

        params: dict[str, Any] = {
            "lifecycle": lifecycle,
            "kanoner_state": state.value,
            "reconstructed": False,
        }
        if channel_test_enabled:
            params["test_mode"] = True

        return Event(
            event_name=event_name,
            params=params,
            ts=source_ts,
            edge_ts=source_ts,
            source=self.source_id,
            tag_id=channel_id,
            severity=severity,
            idempotency_key=idempotency_key,
            quality=(
                Quality.UNCERTAIN if channel_test_enabled else Quality.GOOD
            ),
        )

    @staticmethod
    def _coerce_state(
        mapping: dict[Any, tuple[str, str, EventSeverity]], state: Any
    ) -> Any:
        enum_type = next(iter(mapping))
        if isinstance(state, Enum):
            if type(state) is not type(enum_type):
                raise ValueError(f"unsupported MQTT lifecycle state: {state}")
            return state
        try:
            return type(enum_type)(state)
        except ValueError as exc:
            message = "unsupported MQTT lifecycle state: " + str(state)
            raise ValueError(message) from exc


__all__ = ["MqttLifecycleTracker"]
