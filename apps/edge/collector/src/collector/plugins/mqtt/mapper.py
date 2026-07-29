from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from collector.domain.models import Event, RawSample
from collector.plugins.mqtt.lifecycle_tracker import MqttLifecycleTracker
from collector.plugins.mqtt.payloads import (
    AnalogChannelPayload,
    DiscreteChannelPayload,
    ExhaustGasGroupPayload,
    LogicalEventPayload,
    PayloadUnion,
)


_ANALOG_THRESHOLDS = (
    ("VVU", "threshold_vvu"),
    ("VU", "threshold_vu"),
    ("NU", "threshold_nu"),
    ("NNU", "threshold_nnu"),
)


@dataclass(slots=True)
class MapResult:
    samples: list[RawSample]
    event: Event | None = None
    quarantine_reason: str | None = None


class MqttSemanticMapper:
    """Turn validated MQTT payloads into normalizer-ready raw samples."""

    def __init__(
        self,
        *,
        lifecycle_tracker: MqttLifecycleTracker,
        channel_map: Any,
    ) -> None:
        self._lifecycle_tracker = lifecycle_tracker
        self._channel_map = channel_map

    def map(
        self,
        source_id: str,
        payload: PayloadUnion,
        recv_ts: datetime,
    ) -> MapResult:
        entry = self._lookup(payload.channel_id)
        if entry is None:
            return self._quarantine(source_id, payload, recv_ts)

        source_ts = payload.source_ts or recv_ts
        if isinstance(payload, AnalogChannelPayload):
            samples = self._map_analog(
                source_id, payload, recv_ts, entry, source_ts
            )
            event = self._observe_lifecycle(payload, source_ts)
        elif isinstance(payload, DiscreteChannelPayload):
            samples = [
                self._sample(
                    source_id,
                    payload.channel_id,
                    payload.input_active,
                    recv_ts,
                    source_ts,
                )
            ]
            event = self._observe_lifecycle(payload, source_ts)
        elif isinstance(payload, LogicalEventPayload):
            samples = [
                self._sample(
                    source_id,
                    payload.channel_id,
                    payload.input_active,
                    recv_ts,
                    source_ts,
                )
            ]
            event = self._observe_lifecycle(payload, source_ts)
        elif isinstance(payload, ExhaustGasGroupPayload):
            samples = self._map_egt(
                source_id, payload, recv_ts, source_ts, entry
            )
            event = None
        else:
            raise TypeError(
                f"unsupported MQTT payload: {type(payload).__name__}"
            )

        return MapResult(samples=samples, event=event)

    def _lookup(self, channel_id: str) -> Any:
        lookup = getattr(self._channel_map, "lookup", None)
        if lookup is not None:
            return lookup(channel_id)
        if isinstance(self._channel_map, Mapping):
            return self._channel_map.get(channel_id)
        return None

    def _map_analog(
        self,
        source_id: str,
        payload: AnalogChannelPayload,
        recv_ts: datetime,
        entry: Any,
        source_ts: datetime,
    ) -> list[RawSample]:
        samples = [
            self._sample(
                source_id,
                payload.channel_id,
                payload.value,
                recv_ts,
                source_ts,
            )
        ]
        thresholds = self._value(entry, "thresholds")
        if not self._value(thresholds, "expose", False):
            return samples

        for suffix, field in _ANALOG_THRESHOLDS:
            samples.append(
                self._sample(
                    source_id,
                    f"{payload.channel_id}#{suffix}",
                    getattr(payload, field),
                    recv_ts,
                    source_ts,
                )
            )
        return samples

    def _map_egt(
        self,
        source_id: str,
        payload: ExhaustGasGroupPayload,
        recv_ts: datetime,
        source_ts: datetime,
        entry: Any,
    ) -> list[RawSample]:
        return [
            self._sample(
                source_id,
                f"{payload.channel_id}#CYL{index}.DEV",
                deviation,
                recv_ts,
                source_ts,
            )
            for index, deviation in enumerate(
                payload.cylinder_deviation, start=1
            )
        ]

    def _observe_lifecycle(
        self,
        payload: (
            AnalogChannelPayload | DiscreteChannelPayload | LogicalEventPayload
        ),
        source_ts: datetime,
    ) -> Event | None:
        if isinstance(payload, AnalogChannelPayload):
            state = payload.aps_state
            kind = "analog"
            test_enabled = payload.channel_test_enabled
        elif isinstance(payload, DiscreteChannelPayload):
            state = payload.aps_state
            kind = "discrete"
            test_enabled = payload.channel_test_enabled
        else:
            state = payload.event_state
            kind = "event"
            test_enabled = payload.channel_test_enabled
        return self._lifecycle_tracker.observe(
            payload.channel_id,
            state,
            source_ts,
            kind,
            channel_test_enabled=test_enabled,
        )

    @staticmethod
    def _sample(
        source_id: str,
        native_id: str,
        value: Any,
        recv_ts: datetime,
        source_ts: datetime,
    ) -> RawSample:
        return RawSample(
            source_id=source_id,
            native_id=native_id,
            raw_value=value,
            recv_ts=recv_ts,
            source_ts=source_ts,
        )

    @staticmethod
    def _value(value: Any, key: str, default: Any = None) -> Any:
        if isinstance(value, Mapping):
            return value.get(key, default)
        return getattr(value, key, default)

    def _quarantine(
        self,
        source_id: str,
        payload: PayloadUnion,
        recv_ts: datetime,
    ) -> MapResult:
        value = getattr(payload, "value", None)
        if value is None and hasattr(payload, "input_active"):
            value = payload.input_active
        sample = RawSample(
            source_id=source_id,
            native_id=payload.channel_id,
            raw_value=value,
            native_quality="mqtt.quarantine.unknown_channel",
            recv_ts=recv_ts,
            source_ts=payload.source_ts or recv_ts,
        )
        return MapResult(
            samples=[sample],
            quarantine_reason="unknown_channel",
        )


__all__ = ["MapResult", "MqttSemanticMapper"]
