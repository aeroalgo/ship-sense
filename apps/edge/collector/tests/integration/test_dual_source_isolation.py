from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from collector.config.loader import load_tag_map
from collector.config.models import SourceConfig
from collector.core.restart_policy import RestartPolicy
from collector.core.supervisor import SourceSupervisor
from collector.health.aggregator import HealthAggregator
from collector.plugins.modbus.client import AsyncModbusClient
from collector.plugins.modbus.connector import ModbusTcpConnector
from collector.plugins.opcua.connector import OpcUaConnector
from collector.domain.raw_models import RawSample
from emulator.protocols.modbus_server import ModbusServerAdapter
from emulator.protocols.opcua_server import OpcUaServerAdapter
from emulator.tag_model import TagGenerator

# conftest.py лежит в tests/ и использует parents[4]; этот файл — в tests/integration/,
# поэтому корень репо на один уровень глубже.
ROOT = Path(__file__).parents[5]

# A = OPC UA (будет «убит»), B = Modbus (должен остаться живым).
A_OPCUA = "aps_main_opcua"
B_MODBUS = "aps_main"


async def _drain(queue: asyncio.Queue[RawSample], window: float) -> list[RawSample]:
    """Собрать все сэмплы из очереди за окно window (сек)."""
    out: list[RawSample] = []
    loop = asyncio.get_running_loop()
    deadline = loop.time() + window
    while loop.time() < deadline:
        remaining = deadline - loop.time()
        try:
            out.append(await asyncio.wait_for(queue.get(), timeout=remaining))
        except TimeoutError:
            break
    return out


@pytest.mark.asyncio
async def test_killing_source_a_keeps_b_streaming_and_health_covers_both() -> None:
    """AC-B1-04: падение source A (OPC UA) не роняет поток source B (Modbus).

    Dual protocol: один opcua + один modbus source под двумя SourceSupervisor
    над общей raw_queue. После остановки эмулятора A — B продолжает пушить
    (sample_rate > 0), а агрегированный health отражает оба source_id.
    """
    # Профиль совпадает с tests/conftest.py::modbus_integration (включая STATUS),
    # иначе у ModbusServerAdapter остаётся пустой блок и pymodbus падает при start.
    modbus_profile = {
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
    opcua_profile = {
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

    opcua_emu = OpcUaServerAdapter(TagGenerator(seed=7, profile=opcua_profile))
    modbus_emu = ModbusServerAdapter(TagGenerator(seed=7, profile=modbus_profile))
    await opcua_emu.start(host="127.0.0.1", port=0)
    await modbus_emu.start(host="127.0.0.1", port=0)

    opcua_map = load_tag_map(ROOT / "apps/edge/collector/maps/stub_aps_main_nodes.yaml")
    modbus_map = load_tag_map(ROOT / "apps/edge/collector/maps/stub_aps_main.yaml")

    opcua_cfg = SourceConfig(
        id=A_OPCUA,
        protocol="opcua",
        endpoint=opcua_emu.endpoint,
        subscribe={"publishing_interval_ms": 100},
        readonly_profile=True,
    )
    modbus_cfg = SourceConfig(
        id=B_MODBUS,
        protocol="modbus_tcp",
        endpoint=f"127.0.0.1:{modbus_emu.port}",
        poll={"default_hz": 10.0},
        readonly_profile=True,
    )

    connector_a = OpcUaConnector(opcua_cfg, tag_map=opcua_map)
    connector_b = ModbusTcpConnector(
        modbus_cfg,
        AsyncModbusClient(host="127.0.0.1", port=modbus_emu.port, timeout=1.0),
        modbus_map,
    )

    raw_queue: asyncio.Queue[RawSample] = asyncio.Queue()
    policy = RestartPolicy(initial_backoff_sec=0.01, max_backoff_sec=0.05, jitter=False)
    sup_a = SourceSupervisor(
        connector_a, raw_queue, policy, native_ids=["ns=2;s=AI4104"]
    )
    sup_b = SourceSupervisor(
        connector_b, raw_queue, policy, native_ids=["40107"]
    )

    health = HealthAggregator()

    try:
        await sup_a.start()
        await sup_b.start()

        # Оба источника живы и стримят: дождаться хотя бы по одному сэмплу от каждого.
        seen: set[str] = set()
        for _ in range(100):
            try:
                sample = await asyncio.wait_for(raw_queue.get(), timeout=0.2)
            except TimeoutError:
                break
            seen.add(sample.source_id)
            if {A_OPCUA, B_MODBUS} <= seen:
                break
        assert A_OPCUA in seen, f"source A ({A_OPCUA}) не выдал ни одного сэмпла"
        assert B_MODBUS in seen, f"source B ({B_MODBUS}) не выдал ни одного сэмпла"

        # Агрегированный health до kill: отражает оба источника.
        health.update_source(await connector_a.healthcheck())
        health.update_source(await connector_b.healthcheck())
        snap_before = health.snapshot(collector_state="running")
        health_ids = {s.source_id for s in snap_before.sources}
        assert health_ids == {A_OPCUA, B_MODBUS}

        # --- Kill source A: останавливаем OPC UA эмулятор (транспорт A рвётся). ---
        await opcua_emu.stop()
        # Даём supervisor-у A заметить разрыв и уйти в reconnect/backoff.
        await asyncio.sleep(0.3)

        # Очищаем очередь от сэмплов, накопленных до kill, и меряем B-стрим после.
        while not raw_queue.empty():
            raw_queue.get_nowait()

        post_samples = await _drain(raw_queue, window=1.0)
        b_after_kill = [s for s in post_samples if s.source_id == B_MODBUS]
        assert b_after_kill, (
            "source B остановился после падения source A — изоляция нарушена"
        )

        # Агрегированный health по-прежнему покрывает оба source_id
        # (A теперь в RECONNECTING/DOWN, но всё ещё присутствует в снимке).
        health.update_source(await connector_a.healthcheck())
        health.update_source(await connector_b.healthcheck())
        snap_after = health.snapshot(collector_state="running")
        assert {s.source_id for s in snap_after.sources} == {A_OPCUA, B_MODBUS}
    finally:
        await sup_a.stop()
        await sup_b.stop()
        await modbus_emu.stop()
