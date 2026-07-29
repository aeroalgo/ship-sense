from __future__ import annotations

import asyncio
import json
import random
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class PublishedMessage:
    topic: str
    payload: str
    kind: str


ClientFactory = Callable[[str, int], Any]


class MqttPublisherAdapter:
    """Publish deterministic synthetic MQTT payloads for the emulator."""

    _PANELS = {
        "aps": {
            "analog": "APS.TAI4101",
            "discrete": "APS.DI1401",
            "event": "APS.EV0101",
            "egt": "APS.EGT1",
        },
        "geu": {
            "analog": "GEU.TAI4101",
            "discrete": "GEU.DI2201",
            "event": "GEU.EV0201",
            "egt": "GEU.EGT1",
        },
    }
    _ANALOG_STATES = (
        "normal",
        "exceeded_unacked",
        "returned_unacked",
        "exceeded_acked",
        "blocked",
    )
    _DISCRETE_STATES = (
        "normal",
        "active_unacked",
        "passive_unacked",
        "active_acked",
        "blocked",
    )
    _EVENT_STATES = ("disabled", "enabled", "blocked")
    _EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __init__(
        self,
        panel: str,
        seed: int = 42,
        *,
        interval: float = 1.0,
        client_factory: ClientFactory | None = None,
    ) -> None:
        if panel not in self._PANELS:
            raise ValueError(f"unsupported MQTT panel: {panel}")
        if interval <= 0:
            raise ValueError("interval must be positive")
        self.panel = panel
        self.seed = seed
        self.interval = interval
        self._client_factory = client_factory or self._make_client
        self._client: Any | None = None
        self._client_context: Any | None = None
        self._stop_event = asyncio.Event()
        self._tick = 0

    @property
    def connected(self) -> bool:
        return self._client is not None

    def build_messages(self, tick: int) -> tuple[PublishedMessage, ...]:
        """Build one deterministic message for each supported payload kind."""
        channels = self._PANELS[self.panel]
        rng = random.Random(self.seed + tick)
        source_ts = self._EPOCH + timedelta(seconds=tick)
        analog_state = self._ANALOG_STATES[tick % len(self._ANALOG_STATES)]
        discrete_state = self._DISCRETE_STATES[tick % len(self._DISCRETE_STATES)]
        event_state = self._EVENT_STATES[tick % len(self._EVENT_STATES)]
        analog_value = 60.0 + rng.random() * 10.0

        payloads: tuple[tuple[str, dict[str, Any]], ...] = (
            (
                "analog",
                {
                    "@type": "analog",
                    "schema_version": "1.0",
                    "channel_id": channels["analog"],
                    "source_ts": source_ts.isoformat(),
                    "value": analog_value,
                    "threshold_vvu": 90.0,
                    "threshold_vu": 80.0,
                    "threshold_nu": 40.0,
                    "threshold_nnu": 30.0,
                    "control_vvu": True,
                    "control_vu": True,
                    "control_nu": True,
                    "control_nnu": True,
                    "aps_state": analog_state,
                    "channel_test_enabled": False,
                },
            ),
            (
                "discrete",
                {
                    "@type": "discrete",
                    "schema_version": "1.0",
                    "channel_id": channels["discrete"],
                    "source_ts": source_ts.isoformat(),
                    "aps_state": discrete_state,
                    "input_active": tick % 2 == 1,
                    "channel_test_enabled": False,
                },
            ),
            (
                "event",
                {
                    "@type": "event",
                    "schema_version": "1.0",
                    "channel_id": channels["event"],
                    "source_ts": source_ts.isoformat(),
                    "event_state": event_state,
                    "input_active": tick % 2 == 1,
                    "channel_test_enabled": False,
                },
            ),
            (
                "egt",
                {
                    "@type": "egt",
                    "schema_version": "1.0",
                    "channel_id": channels["egt"],
                    "source_ts": source_ts.isoformat(),
                    "engine_id": channels["egt"],
                    "cylinder_deviation": [
                        round(rng.uniform(-5.0, 5.0), 3) for _ in range(12)
                    ],
                    "engine_mean_temp": 420.0 + rng.random() * 5.0,
                    "max_allowed_deviation": 25.0,
                    "operator_min_mean": 350.0,
                    "operator_max_mean": 500.0,
                    "operator_max_dev_at_min_mean": 20.0,
                    "operator_max_dev_at_max_mean": 25.0,
                    "cylinder_correction": [
                        round(rng.uniform(-1.0, 1.0), 3) for _ in range(12)
                    ],
                    "aps_permission": [True] * 12,
                },
            ),
        )
        return tuple(
            PublishedMessage(
                topic=f"shipsense/v1/{self.panel}/{kind}/{payload['channel_id']}",
                payload=json.dumps(payload, separators=(",", ":"), sort_keys=True),
                kind=kind,
            )
            for kind, payload in payloads
        )

    async def connect(self, broker_url: str) -> None:
        """Connect to an MQTT broker URL, without importing collector code."""
        if self.connected:
            return
        parsed = urlparse(broker_url)
        if parsed.scheme not in {"mqtt", "mqtts"} or not parsed.hostname:
            raise ValueError("broker_url must be mqtt:// or mqtts:// with a host")
        client = self._client_factory(parsed.hostname, parsed.port or 1883)
        self._client_context = client
        self._client = await client.__aenter__()
        self._stop_event.clear()

    async def publish_loop(
        self,
        *,
        iterations: int | None = None,
    ) -> None:
        """Publish at the configured frequency until stopped or iterations finish."""
        client = self._client
        if client is None:
            raise RuntimeError("MQTT publisher is not connected")
        completed = 0
        while not self._stop_event.is_set() and (
            iterations is None or completed < iterations
        ):
            for message in self.build_messages(self._tick):
                await client.publish(message.topic, message.payload, qos=0)
            self._tick += 1
            completed += 1
            if iterations is None or completed < iterations:
                try:
                    await asyncio.wait_for(self._stop_event.wait(), self.interval)
                except TimeoutError:
                    pass

    async def stop(self) -> None:
        """Stop publishing and close the broker context; safe to call repeatedly."""
        self._stop_event.set()
        context, self._client_context = self._client_context, None
        self._client = None
        if context is not None:
            await context.__aexit__(None, None, None)

    @staticmethod
    def _make_client(host: str, port: int) -> Any:
        try:
            import aiomqtt
        except ImportError as exc:
            raise RuntimeError("aiomqtt dependency is not installed") from exc
        return aiomqtt.Client(hostname=host, port=port)


__all__ = ["MqttPublisherAdapter", "PublishedMessage"]
