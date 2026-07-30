from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from collector.config.loader import load_tag_map
from collector.config.models import SourceConfig
from collector.core.restart_policy import RestartPolicy
from collector.core.supervisor import SourceSupervisor
from collector.domain.raw_models import RawSample
from collector.plugins.modbus.client import AsyncModbusClient
from collector.plugins.modbus.connector import ModbusTcpConnector
from emulator.protocols.modbus_server import ModbusServerAdapter
from emulator.tag_model import TagGenerator

pytestmark = pytest.mark.slow

ROOT = Path(__file__).parents[5]


def _live_task_count() -> int:
    current = asyncio.current_task()
    return sum(
        1
        for task in asyncio.all_tasks()
        if not task.done() and task is not current
    )


def _socket_fd_count() -> int:
    fd_root = Path("/proc/self/fd")
    count = 0
    for fd in fd_root.iterdir():
        try:
            if fd.resolve().name.startswith("socket:"):
                count += 1
        except FileNotFoundError:
            continue
    return count


@pytest.mark.asyncio
async def test_modbus_soak_fragment_has_bounded_resources() -> None:
    """Короткий CI soak и ручной 24h прогон не наращивают ресурсы."""
    duration_sec = float(os.getenv("SHIPSENSE_SOAK_DURATION_SEC", "5"))
    drop_interval_sec = float(
        os.getenv("SHIPSENSE_SOAK_DROP_INTERVAL_SEC", "5")
    )
    drop_duration_sec = float(
        os.getenv("SHIPSENSE_SOAK_DROP_DURATION_SEC", "0.2")
    )
    if duration_sec <= 0 or drop_interval_sec <= 0 or drop_duration_sec < 0:
        raise ValueError("soak durations and interval must be positive")

    profile = {
        "id": "soak_stub",
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
        id="soak_modbus",
        protocol="modbus_tcp",
        endpoint=f"127.0.0.1:{emulator.port}",
        poll={"default_hz": 10.0},
        readonly_profile=True,
    )
    connector = ModbusTcpConnector(
        config,
        AsyncModbusClient(host="127.0.0.1", port=emulator.port, timeout=0.2),
        load_tag_map(ROOT / "apps/edge/collector/maps/stub_aps_main.yaml"),
    )
    samples: list[RawSample] = []
    sample_event = asyncio.Event()

    async def on_sample(sample: RawSample) -> None:
        samples.append(sample)
        sample_event.set()

    supervisor = SourceSupervisor(
        connector=connector,
        raw_queue=asyncio.Queue(),
        policy=RestartPolicy(
            initial_backoff_sec=0.02,
            max_backoff_sec=0.1,
            jitter=False,
        ),
        native_ids=["40101", "40107"],
    )
    original_subscribe = connector.subscribe

    async def subscribe_with_sink(
        native_ids: list[str], callback: object
    ) -> object:
        return await original_subscribe(native_ids, on_sample)

    connector.subscribe = subscribe_with_sink  # type: ignore[method-assign]

    baseline_tasks = _live_task_count()
    baseline_sockets = _socket_fd_count()
    try:
        await supervisor.start()
        await asyncio.wait_for(sample_event.wait(), timeout=3.0)
        await asyncio.sleep(0.1)
        steady_tasks = _live_task_count()
        steady_sockets = _socket_fd_count()
        deadline = asyncio.get_running_loop().time() + duration_sec
        next_drop = asyncio.get_running_loop().time() + drop_interval_sec
        drops = 0

        while asyncio.get_running_loop().time() < deadline:
            sleep_sec = max(0.0, next_drop - asyncio.get_running_loop().time())
            await asyncio.sleep(min(0.05, sleep_sec))
            if asyncio.get_running_loop().time() < next_drop:
                continue
            next_drop += drop_interval_sec
            drops += 1
            sample_event.clear()
            await connector.disconnect()
            await emulator.stop()
            await asyncio.sleep(drop_duration_sec)
            await emulator.start(host="127.0.0.1", port=emulator.port)
            await asyncio.wait_for(sample_event.wait(), timeout=3.0)
            await asyncio.sleep(0.05)
            assert _live_task_count() <= steady_tasks + 2
            assert _socket_fd_count() <= steady_sockets + 1

        assert drops >= 1, "soak must exercise at least one connection drop"
        assert samples, "collector did not produce samples"
    finally:
        await supervisor.stop()
        await emulator.stop()
        await asyncio.sleep(0)

    assert _live_task_count() <= baseline_tasks + 1
    assert _socket_fd_count() <= baseline_sockets + 1
