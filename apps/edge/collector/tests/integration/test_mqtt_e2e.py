from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from collector.config.models import (
    MqttConnectionConfig,
    MqttSourceConfig,
    MqttSubscribeConfig,
    TagMapEntry,
)
from collector.core.normalizer import Normalizer
from collector.core.raw_consumer import RawConsumer
from collector.core.restart_policy import RestartPolicy
from collector.core.supervisor import SourceSupervisor
from collector.plugins.mqtt.channel_map import MqttChannelMap
from collector.plugins.mqtt.connector import MqttConnector
from collector.sink.mock_sink import MockSink

ROOT = Path(__file__).parents[5]
COLLECTOR = ROOT / "apps/edge/collector"
FIXTURES = COLLECTOR / "tests/fixtures/mqtt"
APS_MAP = COLLECTOR / "config/maps/mqtt_channels_aps.yaml"
GEU_MAP = COLLECTOR / "config/maps/mqtt_channels_geu.yaml"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_mosquitto_mqtt_collector_emits_sample_and_lifecycle_event(
    mqtt_broker: tuple[str, int],
) -> None:
    host, port = mqtt_broker
    sink = MockSink()
    raw_queue: asyncio.Queue = asyncio.Queue()
    channel_map = MqttChannelMap.load(APS_MAP)
    connector = MqttConnector(
        _source_config("panel_aps", host, port, "aps"),
        channel_map=channel_map,
        on_event=sink.write_event,
    )
    normalizer = _normalizer(channel_map)
    consumer = RawConsumer(raw_queue, sink, normalizer)
    supervisor = SourceSupervisor(
        connector,
        raw_queue,
        RestartPolicy(),
        ["APS.TAI4101"],
    )

    consumer.start()
    await supervisor.start()
    try:
        await _wait_for_subscription(connector)
        async with await _publisher(host, port) as publisher:
            await publisher.publish(
                "shipsense/v1/aps/analog/APS.TAI4101",
                (FIXTURES / "analog.json").read_bytes(),
            )
            await _wait_for_count(sink, samples=5)
            sample = next(
                sample
                for sample in sink.sample_history
                if sample.tag_id == "TAI4101"
            )
            assert sample.value == pytest.approx(82.5)
            assert sample.source_id == "panel_aps"
            assert sink.events == 0

            payload = json.loads((FIXTURES / "analog.json").read_text())
            payload["aps_state"] = "exceeded_unacked"
            payload["source_ts"] = "2026-07-27T12:00:01.000Z"
            await publisher.publish(
                "shipsense/v1/aps/analog/APS.TAI4101",
                json.dumps(payload).encode(),
            )
            await _wait_for_count(sink, samples=10)

        assert sink.events == 1
        assert sink.last_event is not None
        assert sink.last_event.event_name == "aps.threshold.exceeded"
    finally:
        await supervisor.stop()
        await consumer.stop()


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_mosquitto_dual_mqtt_sources_receive_independently(
    mqtt_broker: tuple[str, int],
) -> None:
    host, port = mqtt_broker
    aps_map = MqttChannelMap.load(APS_MAP)
    geu_map = MqttChannelMap.load(GEU_MAP)
    aps_sink = MockSink()
    geu_sink = MockSink()
    aps_queue: asyncio.Queue = asyncio.Queue()
    geu_queue: asyncio.Queue = asyncio.Queue()
    aps_connector = MqttConnector(
        _source_config("panel_aps", host, port, "aps"),
        channel_map=aps_map,
    )
    geu_connector = MqttConnector(
        _source_config("panel_geu", host, port, "geu"),
        channel_map=geu_map,
    )
    aps_consumer = RawConsumer(aps_queue, aps_sink, _normalizer(aps_map))
    geu_consumer = RawConsumer(geu_queue, geu_sink, _normalizer(geu_map))
    aps_supervisor = SourceSupervisor(
        aps_connector, aps_queue, RestartPolicy(), ["APS.TAI4101"]
    )
    geu_supervisor = SourceSupervisor(
        geu_connector, geu_queue, RestartPolicy(), ["GEU.TAI4101"]
    )

    aps_consumer.start()
    geu_consumer.start()
    await aps_supervisor.start()
    await geu_supervisor.start()
    try:
        await _wait_for_subscription(aps_connector)
        await _wait_for_subscription(geu_connector)
        async with await _publisher(host, port) as publisher:
            await publisher.publish(
                "shipsense/v1/aps/analog/APS.TAI4101",
                (FIXTURES / "analog.json").read_bytes(),
            )
            geu_payload = {
                "@type": "analog",
                "schema_version": "1.0",
                "channel_id": "GEU.TAI4101",
                "source_ts": "2026-07-27T12:00:00.000Z",
                "value": 74.0,
                "threshold_vvu": 90.0,
                "threshold_vu": 85.0,
                "threshold_nu": 15.0,
                "threshold_nnu": 10.0,
                "control_vvu": True,
                "control_vu": True,
                "control_nu": False,
                "control_nnu": True,
                "aps_state": "normal",
                "channel_test_enabled": False,
            }
            await publisher.publish(
                "shipsense/v1/geu/analog/GEU.TAI4101",
                json.dumps(geu_payload).encode(),
            )
            await _wait_for_sample(aps_sink)
            await _wait_for_sample(geu_sink)

        assert aps_sink.last_sample is not None
        assert geu_sink.last_sample is not None
        assert aps_sink.last_sample.source_id == "panel_aps"
        assert geu_sink.last_sample.source_id == "panel_geu"
    finally:
        await aps_supervisor.stop()
        await geu_supervisor.stop()
        await aps_consumer.stop()
        await geu_consumer.stop()


def _source_config(
    source_id: str, host: str, port: int, panel: str
) -> MqttSourceConfig:
    return MqttSourceConfig(
        id=source_id,
        protocol="mqtt",
        endpoint=f"mqtt://{host}:{port}",
        connection=MqttConnectionConfig(
            host=host,
            port=port,
            client_id=f"shipsense-test-{source_id}",
        ),
        subscribe=MqttSubscribeConfig(
            topic_prefix=f"shipsense/v1/{panel}/#",
            qos=0,
        ),
        map=f"config/maps/mqtt_channels_{panel}.yaml",
    )


def _normalizer(channel_map: MqttChannelMap) -> Normalizer:
    tag_map = {
        entry.channel_id: TagMapEntry(
            native_id=entry.channel_id,
            tag_id=entry.tag_id,
            datatype=entry.kind,
            unit=entry.unit,
        )
        for entry in channel_map.entries.values()
    }
    return Normalizer.from_yaml(
        tag_map=tag_map,
        quality_rules_path=COLLECTOR / "config/quality_rules.yaml",
        units_path=COLLECTOR / "config/units.yaml",
    )


async def _publisher(host: str, port: int):
    import aiomqtt

    return aiomqtt.Client(
        hostname=host,
        port=port,
        identifier="shipsense-test-publisher",
    )


async def _wait_for_subscription(connector: MqttConnector) -> None:
    for _ in range(100):
        if connector.subscription is not None:
            return
        await asyncio.sleep(0.02)
    raise AssertionError("MQTT connector did not subscribe")


async def _wait_for_sample(sink: MockSink) -> None:
    await _wait_for_count(sink, samples=1)


async def _wait_for_count(sink: MockSink, *, samples: int) -> None:
    for _ in range(100):
        if sink.samples >= samples:
            return
        await asyncio.sleep(0.02)
    raise AssertionError("MQTT sample was not delivered to MockSink")
