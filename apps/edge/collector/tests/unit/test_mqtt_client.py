from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from datetime import datetime
from types import SimpleNamespace
from typing import Any

import pytest

from collector.config.models import (
    MqttConnectionConfig,
    MqttSourceConfig,
    MqttSubscribeConfig,
)
from collector.core.restart_policy import RestartPolicy
from collector.plugins.mqtt.client import (
    AsyncMqttClient,
    MqttConnectionError,
    MqttSubscribeError,
)


class _FakeMessage:
    def __init__(self, topic: Any, payload: bytes) -> None:
        self.topic = topic
        self.payload = payload


class _FakeClient:
    instances: list[_FakeClient] = []

    def __init__(
        self, messages: list[Any], *, fail_enter: bool = False
    ) -> None:
        self.messages = messages
        self.fail_enter = fail_enter
        self.subscriptions: list[tuple[str, int]] = []
        self.entered = False
        self.closed = False
        self._wake = asyncio.Event()
        self.__class__.instances.append(self)

    async def __aenter__(self) -> _FakeClient:
        if self.fail_enter:
            raise ConnectionError("broker unavailable")
        self.entered = True
        return self

    async def __aexit__(self, *_: object) -> None:
        self.closed = True
        self._wake.set()

    async def subscribe(self, topic: str, qos: int = 0) -> None:
        self.subscriptions.append((topic, qos))

    def __aiter__(self) -> AsyncIterator[Any]:
        return self

    async def __anext__(self) -> Any:
        if self.messages:
            item = self.messages.pop(0)
            if isinstance(item, BaseException):
                raise item
            return item
        await self._wake.wait()
        raise StopAsyncIteration


@pytest.fixture
def source_config() -> MqttSourceConfig:
    return MqttSourceConfig(
        id="panel_aps",
        protocol="mqtt",
        endpoint="mqtt://broker:1883",
        connection=MqttConnectionConfig(host="broker", port=1883),
        subscribe=MqttSubscribeConfig(topic_prefix="ship/panel/aps/#", qos=1),
        map="mqtt_panel_aps",
    )


@pytest.mark.asyncio
async def test_connect_subscribe_and_dispatches_bytes(
    source_config: MqttSourceConfig,
) -> None:
    received: list[tuple[str, bytes, datetime]] = []
    fake = _FakeClient([_FakeMessage("ship/panel/aps/temperature", b"42")])
    client = AsyncMqttClient(
        source_config,
        lambda: fake,
        on_message=lambda topic, payload, recv_ts: received.append(
            (topic, payload, recv_ts)
        ),
    )

    await client.connect()
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert client.is_connected()
    assert fake.subscriptions == [("ship/panel/aps/#", 1)]
    assert received[0][0:2] == ("ship/panel/aps/temperature", b"42")
    assert received[0][2].tzinfo is not None

    await client.disconnect()


@pytest.mark.asyncio
async def test_disconnect_reconnects_with_backoff_and_replays_subscription(
    source_config: MqttSourceConfig,
) -> None:
    first = _FakeClient([ConnectionError("connection dropped")])
    second = _FakeClient([])
    clients = iter([first, second])
    client = AsyncMqttClient(
        source_config,
        lambda: next(clients),
        policy=RestartPolicy(
            initial_backoff_sec=0,
            max_backoff_sec=0,
            jitter=False,
        ),
    )

    await client.connect()
    await client.subscribe("ship/panel/aps/#", qos=1)
    await asyncio.wait_for(
        _wait_until(lambda: second.entered and second.subscriptions), timeout=1
    )

    assert second.subscriptions == [("ship/panel/aps/#", 1)]
    await client.disconnect()


@pytest.mark.asyncio
async def test_aiomqtt_topic_object_is_normalized_to_str(
    source_config: MqttSourceConfig,
) -> None:
    from aiomqtt import Topic

    received: list[tuple[str, bytes, datetime]] = []
    fake = _FakeClient(
        [_FakeMessage(Topic("ship/panel/aps/temperature"), b"42")]
    )
    client = AsyncMqttClient(
        source_config,
        lambda: fake,
        on_message=lambda topic, payload, recv_ts: received.append(
            (topic, payload, recv_ts)
        ),
    )

    await client.connect()
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert len(received) == 1
    assert received[0][0:2] == ("ship/panel/aps/temperature", b"42")
    assert isinstance(received[0][0], str)
    await client.disconnect()


@pytest.mark.asyncio
async def test_malformed_message_does_not_stop_consumer(
    source_config: MqttSourceConfig,
) -> None:
    received: list[tuple[str, bytes, datetime]] = []
    fake = _FakeClient(
        [
            SimpleNamespace(topic=None, payload=b"bad"),
            _FakeMessage("ok", b"good"),
        ]
    )
    client = AsyncMqttClient(
        source_config,
        lambda: fake,
        on_message=lambda topic, payload, recv_ts: received.append(
            (topic, payload, recv_ts)
        ),
    )

    await client.connect()
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert len(received) == 1
    assert received[0][0:2] == ("ok", b"good")
    await client.disconnect()


@pytest.mark.asyncio
async def test_connection_and_subscribe_errors_are_typed(
    source_config: MqttSourceConfig,
) -> None:
    failing = _FakeClient([], fail_enter=True)
    client = AsyncMqttClient(source_config, lambda: failing)

    with pytest.raises(MqttConnectionError):
        await client.connect()

    connected = _FakeClient([])
    client = AsyncMqttClient(source_config, lambda: connected)
    await client.connect()
    connected.subscribe = _raise_subscribe

    with pytest.raises(MqttSubscribeError):
        await client.subscribe("topic", qos=1)
    await client.disconnect()


async def _wait_until(predicate: Callable[[], bool]) -> None:
    while not predicate():
        await asyncio.sleep(0)


async def _raise_subscribe(*_: object, **__: object) -> None:
    raise RuntimeError("subscribe failed")
