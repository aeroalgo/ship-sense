from __future__ import annotations

import json

import pytest

from emulator.protocols.mqtt_publisher import MqttPublisherAdapter


class FakeBroker:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []
        self.connected = False

    async def __aenter__(self) -> FakeBroker:
        self.connected = True
        return self

    async def __aexit__(self, *_args: object) -> None:
        self.connected = False

    async def publish(self, topic: str, payload: str, **_kwargs: object) -> None:
        self.messages.append((topic, payload))


@pytest.mark.asyncio
async def test_publisher_emits_all_four_payload_kinds_with_panel_topics() -> None:
    publisher = MqttPublisherAdapter(panel="aps", seed=7)

    messages = publisher.build_messages(tick=0)

    assert {message.kind for message in messages} == {
        "analog",
        "discrete",
        "event",
        "egt",
    }
    for message in messages:
        assert message.topic.startswith("shipsense/v1/aps/")
        payload = json.loads(message.payload)
        assert payload["@type"] == message.kind
        assert payload["schema_version"] == "1.0"


@pytest.mark.asyncio
async def test_publisher_seed_replays_identical_message_sequence() -> None:
    left = MqttPublisherAdapter(panel="geu", seed=42)
    right = MqttPublisherAdapter(panel="geu", seed=42)

    left_messages = [left.build_messages(tick=t) for t in range(3)]
    right_messages = [right.build_messages(tick=t) for t in range(3)]

    assert left_messages == right_messages


@pytest.mark.asyncio
async def test_publish_loop_sends_messages_to_connected_broker() -> None:
    broker = FakeBroker()
    publisher = MqttPublisherAdapter(
        panel="aps",
        seed=7,
        client_factory=lambda _host, _port: broker,
    )

    await publisher.connect("mqtt://localhost:1883")
    await publisher.publish_loop(iterations=1)

    assert broker.connected
    assert len(broker.messages) == 4
    assert all(topic.startswith("shipsense/v1/aps/") for topic, _ in broker.messages)
    assert {json.loads(payload)["@type"] for _, payload in broker.messages} == {
        "analog",
        "discrete",
        "event",
        "egt",
    }

    await publisher.stop()
    assert not broker.connected
