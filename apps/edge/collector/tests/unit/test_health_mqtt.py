"""Tests for MQTT health snapshot fields (AC-MQTT-40)."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from collector.config.models import (
    MqttConnectionConfig,
    MqttSourceConfig,
    MqttSubscribeConfig,
)
from collector.domain.models import HealthStatus, SourceState
from collector.health.aggregator import HealthAggregator
from collector.health.snapshot_writer import SnapshotWriter
from collector.plugins.mqtt.connector import MqttConnector

UTC_NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


class _FakeMqttClient:
    def __init__(self) -> None:
        self.connected = False
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


@pytest.mark.asyncio
async def test_mqtt_healthcheck_exposes_ac_mqtt_40_fields(
    source_config: MqttSourceConfig,
) -> None:
    client = _FakeMqttClient()
    connector = MqttConnector(source_config, client=client)

    await connector.connect()
    await connector.subscribe([], lambda _: None)
    await connector._on_message(
        "shipsense/v1/aps/analog/APS.TAI4101", b"{bad", UTC_NOW
    )

    status = await connector.healthcheck()

    assert status.protocol == "mqtt"
    assert status.connected is True
    assert status.subscribed is True
    assert status.last_msg_ts == UTC_NOW
    assert status.parse_errors == 1
    assert status.broker_reachable is True
    await connector.disconnect()


@pytest.mark.asyncio
async def test_mqtt_health_snapshot_contains_mqtt_fields(
    source_config: MqttSourceConfig,
) -> None:
    client = _FakeMqttClient()
    connector = MqttConnector(source_config, client=client)
    await connector.connect()
    await connector.subscribe([], lambda _: None)
    await connector._on_message(
        "shipsense/v1/aps/analog/APS.TAI4101",
        b'{"@type":"analog","schema_version":"1.0",'
        b'"channel_id":"APS.TAI4101","source_ts":"2026-07-28T12:00:00Z",'
        b'"value":1.0,"threshold_vvu":90.0,"threshold_vu":85.0,'
        b'"threshold_nu":15.0,"threshold_nnu":10.0,"control_vvu":true,'
        b'"control_vu":true,"control_nu":false,"control_nnu":true,'
        b'"aps_state":"normal","channel_test_enabled":false}',
        UTC_NOW,
    )

    agg = HealthAggregator()
    agg.update_source(await connector.healthcheck())
    snap = agg.snapshot(collector_state="running")

    src = next(s for s in snap.sources if s.source_id == "panel_aps")
    assert src.protocol == "mqtt"
    assert src.subscribed is True
    assert src.last_msg_ts == UTC_NOW
    assert src.parse_errors == 0
    assert src.connected is True
    assert src.broker_reachable is True

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "health.json"
        SnapshotWriter(path=path, interval_sec=1).write(snap)
        data = json.loads(path.read_text())
        entry = data["sources"][0]
        assert entry["protocol"] == "mqtt"
        assert entry["subscribed"] is True
        assert entry["last_msg_ts"] == "2026-07-28T12:00:00Z"
        assert entry["parse_errors"] == 0
        assert entry["connected"] is True
        assert entry["broker_reachable"] is True
        assert "collector_state" in data
        assert "samples_total" in data

    await connector.disconnect()


@pytest.mark.asyncio
async def test_parse_errors_increment_reflected_in_snapshot(
    source_config: MqttSourceConfig,
) -> None:
    client = _FakeMqttClient()
    connector = MqttConnector(source_config, client=client)
    await connector.connect()
    await connector.subscribe([], lambda _: None)

    agg = HealthAggregator()
    agg.update_source(await connector.healthcheck())
    assert _source(agg, "panel_aps").parse_errors == 0

    await connector._on_message(
        "shipsense/v1/aps/analog/APS.TAI4101", b"{bad", UTC_NOW
    )
    agg.update_source(await connector.healthcheck())
    assert _source(agg, "panel_aps").parse_errors == 1

    await connector.disconnect()


@pytest.mark.asyncio
async def test_subscribed_false_while_reconnect_in_progress(
    source_config: MqttSourceConfig,
) -> None:
    client = _FakeMqttClient()
    connector = MqttConnector(source_config, client=client)
    await connector.connect()
    await connector.subscribe([], lambda _: None)

    client.connected = False
    connector._subscription = None

    status = await connector.healthcheck()

    assert status.protocol == "mqtt"
    assert status.connected is False
    assert status.subscribed is False
    assert status.broker_reachable is False
    assert status.state is SourceState.DOWN
    await connector.disconnect()


def test_non_mqtt_health_still_serializes_without_mqtt_required_fields() -> None:
    """s14 backward compat: modbus-style HealthStatus still snapshots."""
    agg = HealthAggregator()
    agg.update_source(
        HealthStatus(
            source_id="aps_main",
            state=SourceState.UP,
            last_ok_ts=UTC_NOW,
            reconnect_count=0,
            tags_total=10,
            tags_active=10,
        )
    )
    snap = agg.snapshot(collector_state="running")
    src = snap.sources[0]
    assert src.source_id == "aps_main"
    assert src.protocol is None
    assert src.subscribed is None
    assert src.parse_errors is None


def _source(agg: HealthAggregator, source_id: str) -> Any:
    snap = agg.snapshot(collector_state="running")
    return next(s for s in snap.sources if s.source_id == source_id)
