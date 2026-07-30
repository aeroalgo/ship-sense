from __future__ import annotations

import inspect
import logging
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any, Awaitable

from collector.config.models import MqttSourceConfig
from collector.domain.interfaces import (
    BaseSourceConnector,
    OnSampleCallback,
    Subscription,
)
from collector.domain.health_models import HealthStatus, SourceState
from collector.domain.raw_models import RawSample, RawTagDescriptor
from collector.plugins.mqtt.client import AsyncMqttClient
from collector.plugins.mqtt.lifecycle_tracker import MqttLifecycleTracker
from collector.plugins.mqtt.mapper import MqttSemanticMapper
from collector.plugins.mqtt.parser import MqttParseError, parse_mqtt_payload

logger = logging.getLogger(__name__)

OnEventCallback = Callable[[Any], Awaitable[None] | None]


class MqttConnector(BaseSourceConnector):
    """Subscribe-only MQTT source: transport → parser → semantic mapper."""

    def __init__(
        self,
        config: MqttSourceConfig,
        *,
        client: Any | None = None,
        channel_map: Any | None = None,
        mapper: MqttSemanticMapper | None = None,
        on_sample: Callable[[RawSample], Awaitable[None] | None] | None = None,
        on_event: OnEventCallback | None = None,
    ) -> None:
        super().__init__(config)
        self._mqtt_config = config
        self._channel_map = channel_map if channel_map is not None else {}
        self._lifecycle_tracker = MqttLifecycleTracker(config.id)
        self._mapper = mapper or MqttSemanticMapper(
            lifecycle_tracker=self._lifecycle_tracker,
            channel_map=self._channel_map,
        )
        self._on_sample = on_sample
        self._on_event = on_event
        self._client = client or AsyncMqttClient(
            config, on_message=self._on_message
        )
        self._subscription: Subscription | None = None
        self._connected = False
        self._latest: dict[str, RawSample] = {}
        self.messages_received = 0
        self.parse_errors = 0
        self.last_msg_ts: datetime | None = None

    @property
    def mapper(self) -> MqttSemanticMapper:
        return self._mapper

    @property
    def subscription(self) -> Subscription | None:
        return self._subscription

    async def connect(self) -> None:
        await self._client.connect()
        self._connected = True

    async def disconnect(self) -> None:
        subscription = self._subscription
        self._subscription = None
        if subscription is not None:
            await subscription.cancel()
        await self._client.disconnect()
        self._connected = False

    async def discover_tags(self) -> list[RawTagDescriptor]:
        entries = self._channel_entries()
        return [
            RawTagDescriptor(
                native_id=native_id,
                name=getattr(entry, "tag_id", None),
                unit=getattr(entry, "unit", None),
                datatype=getattr(entry, "datatype", None),
            )
            for native_id, entry in entries
        ]

    async def read(self, native_ids: list[str]) -> list[RawSample]:
        if not native_ids:
            return list(self._latest.values())
        return [
            self._latest[native_id]
            for native_id in native_ids
            if native_id in self._latest
        ]

    async def subscribe(
        self,
        native_ids: list[str],
        on_sample: OnSampleCallback,
    ) -> Subscription:
        self._on_sample = on_sample
        if not self._client_is_connected():
            raise RuntimeError("MQTT client is not connected")
        await self._client.subscribe(
            self._mqtt_config.subscribe.topic_prefix,
            qos=self._mqtt_config.subscribe.qos,
        )
        subscription = Subscription(
            id=f"mqtt:{self.source_id}",
            tag_ids=list(native_ids),
        )
        self._subscription = subscription
        return subscription

    async def healthcheck(self) -> HealthStatus:
        connected = self._connected and self._client_is_connected()
        broker_reachable = self._client_is_connected()
        subscribed = self._subscription is not None and connected
        return HealthStatus(
            source_id=self.source_id,
            state=self._compute_state(),
            last_ok_ts=self.last_msg_ts,
            reconnect_count=self._reconnect_count,
            protocol="mqtt",
            connected=connected,
            subscribed=subscribed,
            last_msg_ts=self.last_msg_ts,
            parse_errors=self.parse_errors,
            broker_reachable=broker_reachable,
            detail=(
                f"messages_received={self.messages_received};"
                f"parse_errors={self.parse_errors}"
            ),
        )

    async def _on_message(
        self, topic: str, payload: bytes, recv_ts: datetime
    ) -> None:
        self.messages_received += 1
        self.last_msg_ts = recv_ts
        try:
            parsed = parse_mqtt_payload(topic, payload)
            result = self._mapper.map(self.source_id, parsed, recv_ts)
        except MqttParseError as exc:
            self.parse_errors += 1
            logger.warning(
                "MQTT payload rejected for %s: %s", self.source_id, exc
            )
            return

        for sample in result.samples:
            self._latest[sample.native_id] = sample
            await self._emit_sample(sample)
        if result.event is not None and self._on_event is not None:
            await _maybe_await(self._on_event(result.event))

    async def _emit_sample(self, sample: RawSample) -> None:
        if self._on_sample is not None:
            await _maybe_await(self._on_sample(sample))

    def _client_is_connected(self) -> bool:
        connected = getattr(self._client, "is_connected", False)
        return bool(connected() if callable(connected) else connected)

    def _compute_state(self) -> SourceState:
        if self._connected and self._client_is_connected():
            return SourceState.UP
        return SourceState.DOWN

    def _channel_entries(self) -> list[tuple[str, Any]]:
        if isinstance(self._channel_map, Mapping):
            return list(self._channel_map.items())
        entries = getattr(self._channel_map, "entries", None)
        if isinstance(entries, Mapping):
            return list(entries.items())
        return []


async def _maybe_await(value: Any) -> None:
    if inspect.isawaitable(value):
        await value


__all__ = ["MqttConnector"]
