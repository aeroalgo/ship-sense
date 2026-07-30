from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio

try:
    from testcontainers.community.mqtt import MosquittoContainer
except ImportError:  # pragma: no cover - integration dependency
    MosquittoContainer = None

try:
    import aiomqtt  # noqa: F401
except ImportError:  # pragma: no cover - integration dependency
    aiomqtt = None

from collector.config.loader import load_tag_map
from collector.config.models import SourceConfig
from collector.domain.models import Quality, RawSample, TelemetrySample
from collector.plugins.modbus.client import AsyncModbusClient
from collector.plugins.modbus.connector import ModbusTcpConnector
from collector.plugins.opcua.connector import OpcUaConnector
from emulator.protocols.modbus_server import ModbusServerAdapter
from emulator.protocols.opcua_server import OpcUaServerAdapter
from emulator.tag_model import TagGenerator


class IntegrationSink:
    def __init__(self) -> None:
        self.samples: list[TelemetrySample] = []
        self.sample_event = asyncio.Event()

    async def raw_callback(self, sample: RawSample) -> None:
        value = (
            sample.raw_value
            if isinstance(sample.raw_value, (int, float, bool, str))
            else None
        )
        self.samples.append(
            TelemetrySample(
                tag_id={
                    "40101": "TAI4101",
                    "40107": "TAI4104",
                }[sample.native_id],
                value=value,
                unit={"40101": "degC", "40107": "rpm"}[sample.native_id],
                source_ts=sample.recv_ts,
                edge_ts=sample.recv_ts,
                quality=(
                    Quality.GOOD
                    if sample.native_quality == "good"
                    else Quality.BAD
                ),
                source_id=sample.source_id,
                native_id=sample.native_id,
            )
        )
        self.sample_event.set()


@pytest_asyncio.fixture
async def modbus_integration() -> AsyncIterator[
    tuple[ModbusTcpConnector, IntegrationSink]
]:
    root = Path(__file__).parents[4]
    profile = {
        "id": "aps_stub",
        "tick_hz": 10.0,
        "signals": [
            {
                "signal_id": "MAIN_ENGINE_TEMP",
                "native_ids": {"modbus": "40101"},
                "value_type": "float32",
                "generator": {"kind": "constant", "value": 75.0},
            },
            {
                "signal_id": "MAIN_ENGINE_RPM",
                "native_ids": {"modbus": "40107"},
                "value_type": "float32",
                "generator": {"kind": "constant", "value": 1800.0},
            },
            {
                "signal_id": "STATUS",
                "native_ids": {"modbus": "41000"},
                "value_type": "boolean",
                "generator": {"kind": "constant", "value": True},
            },
        ],
    }
    generator = TagGenerator(seed=7, profile=profile)
    emulator = ModbusServerAdapter(generator)
    await emulator.start(host="127.0.0.1", port=0)

    config = SourceConfig(
        id="aps_main",
        protocol="modbus_tcp",
        endpoint=f"127.0.0.1:{emulator.port}",
        poll={"default_hz": 10.0},
        readonly_profile=True,
    )
    tag_map = load_tag_map(
        root / "apps/edge/collector/maps/stub_aps_main.yaml"
    )
    connector = ModbusTcpConnector(
        config,
        AsyncModbusClient(host="127.0.0.1", port=emulator.port, timeout=1.0),
        tag_map,
    )
    sink = IntegrationSink()
    try:
        yield connector, sink
    finally:
        await connector.disconnect()
        await emulator.stop()


class OpcuaIntegrationSink:
    """Sink для OPC UA integration.

    native_quality `opcua.Good` → Quality.GOOD.
    """

    _TAG_BY_NODE = {
        "ns=2;s=AI4101": "TAI4101",
        "ns=2;s=AI4104": "TAI4104",
    }
    _UNIT_BY_NODE = {
        "ns=2;s=AI4101": "degC",
        "ns=2;s=AI4104": "rpm",
    }

    def __init__(self) -> None:
        self.samples: list[TelemetrySample] = []
        self.sample_event = asyncio.Event()

    async def raw_callback(self, sample: RawSample) -> None:
        value = (
            sample.raw_value
            if isinstance(sample.raw_value, (int, float, bool, str))
            else None
        )
        native_quality = sample.native_quality or ""
        self.samples.append(
            TelemetrySample(
                tag_id=self._TAG_BY_NODE[sample.native_id],
                value=value,
                unit=self._UNIT_BY_NODE[sample.native_id],
                source_ts=sample.recv_ts,
                edge_ts=sample.recv_ts,
                quality=(
                    Quality.GOOD
                    if native_quality in ("opcua.Good", None, "")
                    else Quality.BAD
                ),
                source_id=sample.source_id,
                native_id=sample.native_id,
            )
        )
        self.sample_event.set()


@pytest_asyncio.fixture
async def opcua_integration() -> AsyncIterator[
    tuple[OpcUaConnector, OpcuaIntegrationSink, OpcUaServerAdapter]
]:
    root = Path(__file__).parents[4]
    profile = {
        "id": "aps_stub",
        "tick_hz": 10.0,
        "signals": [
            {
                "signal_id": "MAIN_ENGINE_TEMP",
                "native_ids": {"opcua": "ns=2;s=AI4101"},
                "value_type": "float32",
                "generator": {"kind": "constant", "value": 75.0},
            },
            {
                "signal_id": "MAIN_ENGINE_RPM",
                "native_ids": {"opcua": "ns=2;s=AI4104"},
                "value_type": "float32",
                "generator": {"kind": "constant", "value": 1800.0},
            },
        ],
    }
    generator = TagGenerator(seed=7, profile=profile)
    emulator = OpcUaServerAdapter(generator)
    await emulator.start(host="127.0.0.1", port=0)

    config = SourceConfig(
        id="aps_main_opcua",
        protocol="opcua",
        endpoint=emulator.endpoint,
        subscribe={"publishing_interval_ms": 100},
        readonly_profile=True,
    )
    tag_map = load_tag_map(
        root / "apps/edge/collector/maps/stub_aps_main_nodes.yaml"
    )
    connector = OpcUaConnector(config, tag_map=tag_map)
    sink = OpcuaIntegrationSink()
    try:
        yield connector, sink, emulator
    finally:
        await connector.disconnect()
        await emulator.stop()


@pytest.fixture(scope="module")
def mqtt_broker() -> tuple[str, int]:
    """Start an ephemeral Mosquitto broker for MQTT integration tests."""
    if MosquittoContainer is None or aiomqtt is None:
        pytest.skip("MQTT integration dependencies are not installed")
    import concurrent.futures

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                lambda: MosquittoContainer("eclipse-mosquitto:2").start()
            )
            broker = future.result(timeout=60)
    except concurrent.futures.TimeoutError:
        pytest.fail("MosquittoContainer.start timed out after 60s")
    except Exception as exc:
        pytest.skip(f"Mosquitto container is unavailable: {exc}")
    try:
        host = broker.get_container_host_ip()
        port = int(broker.get_exposed_port(1883))
        yield host, port
    finally:
        broker.stop()
