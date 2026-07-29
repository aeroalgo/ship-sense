from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from collector.app import CollectorApp
from collector.config.models import SourceConfig
from collector.domain.models import RawSample
from collector.health.aggregator import HealthAggregator
from collector.health.snapshot_writer import SnapshotWriter
from collector.runtime.endpoints import parse_writer_endpoint
from emulator.protocols.opcua_server import _coerce_value


class _Sink:
    async def write_sample(self, sample) -> None:
        return None

    async def write_event(self, event) -> None:
        return None


class _Supervisor:
    state = "up"

    def __init__(self, source_id: str) -> None:
        self._source_id = source_id
        self.started = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        return None

    async def healthcheck(self):
        from collector.domain.models import HealthStatus, SourceState

        return HealthStatus(source_id=self._source_id, state=SourceState.UP)


async def _normalize(sample: RawSample):
    return None


def test_parse_writer_endpoint() -> None:
    assert parse_writer_endpoint("writer:9009") == ("writer", 9009)


@pytest.mark.parametrize("value_type,value,expected", [
    ("float32", 1.25, 1.25),
    ("int16", 12.75, 12),
    ("boolean", 1, True),
    ("string", 42, "42"),
])
def test_coerce_value_matches_declared_variant_type(
    value_type: str, value: object, expected: object
) -> None:
    assert _coerce_value(value, value_type) == expected


@pytest.mark.asyncio
async def test_snapshot_writer_writes_while_collector_is_running(tmp_path: Path) -> None:
    path = tmp_path / "health" / "collector.json"
    health = HealthAggregator()
    supervisor = _Supervisor("aps_main")
    writer = SnapshotWriter(path=path, interval_sec=0.01)
    app = CollectorApp(
        raw_queue=asyncio.Queue(),
        sink=_Sink(),
        normalize=_normalize,
        sources=[],
        supervisors=[supervisor],
        health=health,
        snapshot_writer=writer,
    )

    await app.start()
    await asyncio.sleep(0.03)
    assert path.exists()
    assert json.loads(path.read_text())["collector_state"] == "running"
    await app.stop()


def test_source_filter_uses_csv_ids() -> None:
    from collector.runtime.bootstrap import filter_sources

    sources = [
        SourceConfig(id="a", protocol="modbus_tcp", endpoint="a:1"),
        SourceConfig(id="b", protocol="modbus_tcp", endpoint="b:2"),
    ]
    assert [source.id for source in filter_sources(sources, "b")] == ["b"]
    assert [source.id for source in filter_sources(sources, None)] == ["a", "b"]
