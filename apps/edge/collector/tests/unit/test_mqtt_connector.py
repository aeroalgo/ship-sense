from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from collector.config.models import (
    MqttConnectionConfig,
    MqttSourceConfig,
    MqttSubscribeConfig,
    TagMapEntry,
)
from collector.domain.raw_models import RawSample
from collector.plugins.mqtt.connector import MqttConnector
from collector.plugins.mqtt.mapper import MqttSemanticMapper
from collector.plugins.registry import PluginRegistry


UTC_NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


class _FakeMqttClient:
    def __init__(self) -> None:
        self.connected = False
        self.callback: Any = None
        self.subscriptions: list[tuple[str, int]] = []

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def subscribe(self, topic_filter: str, qos: int = 0) -> None:
        self.subscriptions.append((topic_filter, qos))

    def is_connected(self) -> bool:
        return self.connected


@pytest.fixture
def source_config() -> MqttSourceConfig:
    return MqttSourceConfig(
        id="panel_aps",
        protocol="mqtt",
        endpoint="mqtt://broker:1883",
        connection=MqttConnectionConfig(host="broker"),
        subscribe=MqttSubscribeConfig(
            topic_prefix="shipsense/v1/aps/#", qos=1
        ),
        map="mqtt_panel_aps",
    )


@pytest.fixture
def registry() -> type[PluginRegistry]:
    saved = dict(PluginRegistry._plugins)
    PluginRegistry._plugins.clear()
    yield PluginRegistry
    PluginRegistry._plugins.clear()
    PluginRegistry._plugins.update(saved)


def test_registry_create_mqtt_returns_connector(
    registry: type[PluginRegistry], source_config: MqttSourceConfig
) -> None:
    registry.register("mqtt", MqttConnector)

    connector = registry.create(source_config)

    assert isinstance(connector, MqttConnector)
    assert connector.protocol == "mqtt"
    assert connector.source_id == "panel_aps"


@pytest.mark.asyncio
async def test_message_is_parsed_mapped_and_sent_to_callback(
    source_config: MqttSourceConfig,
) -> None:
    client = _FakeMqttClient()
    samples: list[RawSample] = []
    connector = MqttConnector(
        source_config,
        client=client,
        channel_map={
            "APS.TAI4101": TagMapEntry(
                native_id="APS.TAI4101",
                tag_id="TAI4101",
                datatype="float",
                unit="degC",
            )
        },
        on_sample=samples.append,
    )

    await connector.connect()
    subscription = await connector.subscribe([], samples.append)
    await connector._on_message(
        "shipsense/v1/aps/analog/APS.TAI4101",
        b'{"@type":"analog","schema_version":"1.0",'
        b'"channel_id":"APS.TAI4101","source_ts":"2026-07-28T12:00:00Z",'
        b'"value":82.5,"threshold_vvu":90.0,"threshold_vu":85.0,'
        b'"threshold_nu":15.0,"threshold_nnu":10.0,"control_vvu":true,'
        b'"control_vu":true,"control_nu":false,"control_nnu":true,'
        b'"aps_state":"normal","channel_test_enabled":false}',
        UTC_NOW,
    )

    assert subscription.tag_ids == []
    assert client.subscriptions == [("shipsense/v1/aps/#", 1)]
    assert samples[0].native_id == "APS.TAI4101"
    assert samples[0].raw_value == 82.5
    assert connector.messages_received == 1
    assert connector.parse_errors == 0
    await connector.disconnect()


@pytest.mark.asyncio
async def test_malformed_json_increments_metric_and_connector_stays_alive(
    source_config: MqttSourceConfig,
) -> None:
    client = _FakeMqttClient()
    connector = MqttConnector(source_config, client=client)

    await connector.connect()
    await connector.subscribe([], lambda _: None)
    await connector._on_message(
        "shipsense/v1/aps/analog/APS.TAI4101", b"{bad", UTC_NOW
    )

    assert connector.parse_errors == 1
    assert connector.messages_received == 1
    assert client.connected
    await connector.disconnect()


@pytest.mark.asyncio
async def test_two_connectors_keep_independent_metrics(
    source_config: MqttSourceConfig,
) -> None:
    first = MqttConnector(source_config, client=_FakeMqttClient())
    second = MqttConnector(
        source_config.model_copy(update={"id": "panel_geu"}),
        client=_FakeMqttClient(),
    )

    await first.connect()
    await second.connect()
    await first._on_message(
        "shipsense/v1/aps/analog/APS.TAI4101", b"{bad", UTC_NOW
    )

    assert first.parse_errors == 1
    assert second.parse_errors == 0
    assert first.source_id != second.source_id
    await first.disconnect()
    await second.disconnect()


def test_connector_uses_mapper_pipeline(
    source_config: MqttSourceConfig,
) -> None:
    connector = MqttConnector(source_config, client=_FakeMqttClient())

    assert isinstance(connector.mapper, MqttSemanticMapper)
    assert connector.subscription is None
