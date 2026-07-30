"""L1 MQTT pipeline → DB rows (T-002 s04).

MQTT publish → Mosquitto (testcontainers) → MqttConnector + Normalizer + Supervisor
→ IpcCanonicalSink → WriterService → samples/events.

Markers: integration + slow (Docker required).
AC: AC-PIPE-03 (samples), AC-PIPE-04 (events) — этот файл покрывает оба.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import text

from apps.edge.collector.src.collector.domain.models import Quality
from apps.edge.collector.src.collector.sink.ipc_sink import IpcCanonicalSink
from apps.edge.storage.writer import WriterService

# Paths
ROOT = Path(__file__).parents[2]
COLLECTOR = ROOT / "apps/edge/collector"
APS_MAP = COLLECTOR / "config/maps/mqtt_channels_aps.yaml"
APS_FIXTURE = COLLECTOR / "tests/fixtures/mqtt/analog.json"

# Fixed UTC timestamp for determinism (align with writer_ipc_db)
UTC_TS = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)

# Poll (longer wall clock for L1: container startup + reconnect)
POLL_TIMEOUT_S = 30.0
POLL_INTERVAL_S = 0.1


def _passthrough_normalize(sample):
    """Minimal passthrough to match writer_ipc_db pattern (B4 normalization later)."""
    from apps.edge.collector.src.collector.domain.models import TelemetrySample

    return TelemetrySample(
        tag_id=sample.native_id,
        value=sample.raw_value if isinstance(sample.raw_value, (int, float, str, bool)) else None,
        unit="unknown",
        source_ts=sample.source_ts or sample.recv_ts,
        edge_ts=sample.recv_ts,
        quality=Quality.GOOD,
        source_id=sample.source_id,
        native_id=sample.native_id,
    )


async def _poll_until(
    db_session,
    query: str,
    expected_min: int = 1,
    timeout_s: float = POLL_TIMEOUT_S,
    interval_s: float = POLL_INTERVAL_S,
) -> int:
    """Poll SELECT COUNT(*) until >= expected_min or timeout.

    Returns count on success. Raises AssertionError with message on timeout.
    """
    deadline = asyncio.get_event_loop().time() + timeout_s
    last_count = 0
    while True:
        result = await db_session.execute(text(query))
        count = result.scalar_one()
        last_count = int(count)
        if last_count >= expected_min:
            return last_count
        if asyncio.get_event_loop().time() >= deadline:
            raise AssertionError(
                f"timeout after {timeout_s}s: query={query!r} last_count={last_count} expected>={expected_min}"
            )
        await asyncio.sleep(interval_s)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_mqtt_emulator_persists_analog_to_db(
    mqtt_broker: tuple[str, int],
    writer_endpoint: tuple[str, int],
    db_session,
) -> None:
    """AC-PIPE-03: MQTT publish → collector stack → writer → samples.tag_id='TAI4101' COUNT≥1.

    Uses collector stack (MqttConnector + Normalizer + SourceSupervisor + IpcCanonicalSink)
    wired to real WriterService (from writer_endpoint fixture) + TimescaleDB.

    Pattern mirrors test_mosquitto_mqtt_collector_emits_sample_and_lifecycle_event
    but replaces MockSink with IpcCanonicalSink(writer_endpoint).
    """
    from collector.config.models import (
        MqttConnectionConfig,
        MqttSourceConfig,
        MqttSubscribeConfig,
    )
    from collector.core.normalizer import Normalizer
    from collector.core.raw_consumer import RawConsumer
    from collector.core.restart_policy import RestartPolicy
    from collector.core.supervisor import SourceSupervisor
    from collector.plugins.mqtt.channel_map import MqttChannelMap
    from collector.plugins.mqtt.connector import MqttConnector

    host, port = mqtt_broker
    writer_host, writer_port = writer_endpoint

    # Channel map + normalizer (real, from collector config)
    channel_map = MqttChannelMap.load(APS_MAP)
    # Convert MqttChannelMapEntry -> TagMapEntry (required by Normalizer/QualityEngine)
    # See collector/tests/integration/test_mqtt_e2e.py::_normalizer for pattern
    from collector.config.models import TagMapEntry

    tag_map = {
        entry.channel_id: TagMapEntry(
            native_id=entry.channel_id,
            tag_id=entry.tag_id,
            datatype=entry.kind,
            unit=entry.unit,
        )
        for entry in channel_map.entries.values()
    }
    normalizer = Normalizer.from_yaml(
        tag_map=tag_map,
        quality_rules_path=COLLECTOR / "config/quality_rules.yaml",
        units_path=COLLECTOR / "config/units.yaml",
    )

    # Sink = real IPC to writer (no mocks on insert_batch)
    sink = IpcCanonicalSink(endpoint=(writer_host, writer_port))

    # Raw queue + consumer
    raw_queue: asyncio.Queue = asyncio.Queue()
    consumer = RawConsumer(raw_queue, sink, normalizer)

    # Supervisor + connector (single tag for minimal wiring)
    connector = MqttConnector(
        MqttSourceConfig(
            id="panel_aps",
            protocol="mqtt",
            endpoint=f"mqtt://{host}:{port}",
            connection=MqttConnectionConfig(
                host=host,
                port=port,
                client_id="shipsense-test-mqtt-pipeline",
            ),
            subscribe=MqttSubscribeConfig(
                topic_prefix="shipsense/v1/aps/#",
                qos=0,
            ),
            map=str(APS_MAP),
        ),
        channel_map=channel_map,
    )

    supervisor = SourceSupervisor(
        connector,
        raw_queue,
        RestartPolicy(),
        ["APS.TAI4101"],
    )

    # Start consumer + supervisor
    consumer.start()
    await supervisor.start()

    try:
        # Wait for subscription
        for _ in range(200):
            if connector.subscription is not None:
                break
            await asyncio.sleep(0.02)
        else:
            raise AssertionError("MQTT connector did not subscribe")

        # Publish N iterations via aiomqtt (same pattern as collector e2e test)
        import json

        import aiomqtt

        payload = json.loads(APS_FIXTURE.read_text())
        async with aiomqtt.Client(
            hostname=host,
            port=port,
            identifier="shipsense-test-publisher-pipeline",
        ) as publisher:
            for _ in range(3):
                await publisher.publish(
                    "shipsense/v1/aps/analog/APS.TAI4101",
                    json.dumps(payload).encode(),
                )
                await asyncio.sleep(0.05)

        # Flush sink to ensure IPC delivery
        await sink.flush()
        await sink.close()

        # Poll DB until at least one sample with tag_id='TAI4101'
        count = await _poll_until(
            db_session,
            query="SELECT COUNT(*) FROM samples WHERE tag_id='TAI4101'",
            expected_min=1,
        )
        assert count >= 1

        # Verify value approx (from fixture)
        row = await db_session.execute(
            text(
                "SELECT value FROM samples "
                "WHERE tag_id='TAI4101' ORDER BY edge_ts DESC LIMIT 1"
            )
        )
        value = row.scalar_one()
        assert value == pytest.approx(82.5, abs=0.01)

    finally:
        await supervisor.stop()
        await consumer.stop()


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_mqtt_lifecycle_persists_event_to_db(
    mqtt_broker: tuple[str, int],
    writer_endpoint: tuple[str, int],
    db_session,
) -> None:
    """AC-PIPE-04: MQTT publish lifecycle transition → collector stack → writer → events.

    Mirrors test_mosquitto_mqtt_collector_emits_sample_and_lifecycle_event but wires
    through IpcCanonicalSink (on_event) + WriterService + TimescaleDB.

    Publish normal → no event; then exceeded_unacked → event 'aps.threshold.exceeded'
    is delivered via on_event → IPC → writer → events table (COUNT>=1).
    """
    from collector.config.models import (
        MqttConnectionConfig,
        MqttSourceConfig,
        MqttSubscribeConfig,
    )
    from collector.core.normalizer import Normalizer
    from collector.core.raw_consumer import RawConsumer
    from collector.core.restart_policy import RestartPolicy
    from collector.core.supervisor import SourceSupervisor
    from collector.plugins.mqtt.channel_map import MqttChannelMap
    from collector.plugins.mqtt.connector import MqttConnector

    host, port = mqtt_broker
    writer_host, writer_port = writer_endpoint

    # Channel map + normalizer (real)
    channel_map = MqttChannelMap.load(APS_MAP)
    from collector.config.models import TagMapEntry

    tag_map = {
        entry.channel_id: TagMapEntry(
            native_id=entry.channel_id,
            tag_id=entry.tag_id,
            datatype=entry.kind,
            unit=entry.unit,
        )
        for entry in channel_map.entries.values()
    }
    normalizer = Normalizer.from_yaml(
        tag_map=tag_map,
        quality_rules_path=COLLECTOR / "config/quality_rules.yaml",
        units_path=COLLECTOR / "config/units.yaml",
    )

    # Sink = real IPC to writer (receives both samples and events)
    sink = IpcCanonicalSink(endpoint=(writer_host, writer_port))

    # Raw queue + consumer
    raw_queue: asyncio.Queue = asyncio.Queue()
    consumer = RawConsumer(raw_queue, sink, normalizer)

    # Supervisor + connector — IMPORTANT: pass on_event so lifecycle events flow via IPC
    connector = MqttConnector(
        MqttSourceConfig(
            id="panel_aps",
            protocol="mqtt",
            endpoint=f"mqtt://{host}:{port}",
            connection=MqttConnectionConfig(
                host=host,
                port=port,
                client_id="shipsense-test-mqtt-pipeline-lifecycle",
            ),
            subscribe=MqttSubscribeConfig(
                topic_prefix="shipsense/v1/aps/#",
                qos=0,
            ),
            map=str(APS_MAP),
        ),
        channel_map=channel_map,
        on_event=sink.write_event,
    )

    supervisor = SourceSupervisor(
        connector,
        raw_queue,
        RestartPolicy(),
        ["APS.TAI4101"],
    )

    # Start consumer + supervisor
    consumer.start()
    await supervisor.start()

    try:
        # Wait for subscription
        for _ in range(200):
            if connector.subscription is not None:
                break
            await asyncio.sleep(0.02)
        else:
            raise AssertionError("MQTT connector did not subscribe")

        import json

        import aiomqtt

        # Base payload (normal state)
        payload = json.loads(APS_FIXTURE.read_text())

        async with aiomqtt.Client(
            hostname=host,
            port=port,
            identifier="shipsense-test-publisher-lifecycle",
        ) as publisher:
            # Publish normal — establishes state, no lifecycle event expected
            await publisher.publish(
                "shipsense/v1/aps/analog/APS.TAI4101",
                json.dumps(payload).encode(),
            )
            await asyncio.sleep(0.1)

            # Transition to exceeded_unacked (new ts) → should emit aps.threshold.exceeded
            payload["aps_state"] = "exceeded_unacked"
            payload["source_ts"] = "2026-07-27T12:00:01.000Z"
            await publisher.publish(
                "shipsense/v1/aps/analog/APS.TAI4101",
                json.dumps(payload).encode(),
            )
            await asyncio.sleep(0.1)

        # Ensure delivery
        await sink.flush()
        await sink.close()

        # Poll DB for the lifecycle event
        count = await _poll_until(
            db_session,
            query="SELECT COUNT(*) FROM events WHERE event_name='aps.threshold.exceeded'",
            expected_min=1,
        )
        assert count >= 1

    finally:
        await supervisor.stop()
        await consumer.stop()
