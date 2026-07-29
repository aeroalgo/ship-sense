"""Tests for HealthAggregator, SnapshotWriter, metrics (AC-B1-07, AC-B1-12, AC-HLT-01..03, AC-HLT-05)."""

from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from collector.domain.models import (
    CollectorHealthSnapshot,
    HealthStatus,
    SourceState,
)
from collector.health.aggregator import HealthAggregator
from collector.health.metrics import Metrics
from collector.health.snapshot_writer import SnapshotWriter


UTC_NOW = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)


def _health(source_id: str, state: SourceState = SourceState.UP) -> HealthStatus:
    return HealthStatus(
        source_id=source_id,
        state=state,
        last_ok_ts=UTC_NOW,
        reconnect_count=0,
        tags_total=10,
        tags_active=10,
    )


# ---------------------------------------------------------------
# Metrics (AC-HLT-03)
# ---------------------------------------------------------------
def test_metrics_bump_and_read() -> None:
    """Metrics: счётчики samples_in/out/errors; queue_depth задаётся снаружи."""
    m = Metrics()
    m.bump_samples_in(3)
    m.bump_samples_out(2)
    m.bump_errors(1)

    assert m.samples_in == 3
    assert m.samples_out == 2
    assert m.errors == 1

    m.bump_samples_in()
    assert m.samples_in == 4


def test_metrics_queue_depths_are_setters() -> None:
    """Queue depths — внешние (от RawConsumer/QueueSink), не внутри Metrics."""
    m = Metrics()
    m.set_queue_depths(raw=5, canonical=1)

    assert m.queue_raw_depth == 5
    assert m.queue_canonical_depth == 1


# ---------------------------------------------------------------
# HealthAggregator (AC-B1-07, AC-B1-12)
# ---------------------------------------------------------------
def test_health_aggregator_update_source_and_snapshot() -> None:
    """Aggregator собирает per-source health + глобальные счётчики → snapshot."""
    agg = HealthAggregator()
    agg.update_source(_health("aps_main", SourceState.UP))
    agg.update_source(_health("skt_geu", SourceState.DEGRADED))

    agg.bump_samples_in(10)
    agg.bump_samples_out(9)
    agg.bump_errors(1)
    agg.set_queue_depths(raw=2, canonical=1)

    snap = agg.snapshot(collector_state="running")

    assert isinstance(snap, CollectorHealthSnapshot)
    assert snap.collector_state == "running"
    assert len(snap.sources) == 2
    assert {s.source_id for s in snap.sources} == {"aps_main", "skt_geu"}
    assert snap.samples_total == 10
    assert snap.events_total == 0
    assert snap.errors_total == 1
    assert snap.queue_raw_depth == 2
    assert snap.queue_canonical_depth == 1


def test_health_aggregator_overwrites_source_on_update() -> None:
    """Повторный update_source для того же source_id перезаписывает статус."""
    agg = HealthAggregator()
    agg.update_source(_health("aps_main", SourceState.UP))
    agg.update_source(_health("aps_main", SourceState.RECONNECTING))

    snap = agg.snapshot(collector_state="running")

    src = next(s for s in snap.sources if s.source_id == "aps_main")
    assert src.state is SourceState.RECONNECTING


def test_health_aggregator_snapshot_ts_is_fresh() -> None:
    """snapshot() проставляет свежий ts (UTC)."""
    agg = HealthAggregator()
    before = datetime.now(timezone.utc)
    snap = agg.snapshot(collector_state="starting")
    after = datetime.now(timezone.utc)

    assert before <= snap.ts <= after
    assert snap.ts.tzinfo is not None


# ---------------------------------------------------------------
# SnapshotWriter (AC-HLT-02)
# ---------------------------------------------------------------
def test_snapshot_writer_writes_json_file() -> None:
    """SnapshotWriter пишет JSON-файл по пути; содержимое — валидный snapshot."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "health.json"
        writer = SnapshotWriter(path=path, interval_sec=1)

        agg = HealthAggregator()
        agg.update_source(_health("aps_main"))

        writer.write(agg.snapshot(collector_state="running"))

        assert path.exists()
        data = json.loads(path.read_text())
        assert data["collector_state"] == "running"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["source_id"] == "aps_main"


def test_snapshot_writer_is_idempotent_on_missing_parent_dir(tmp_path: Path) -> None:
    """Writer создаёт родительскую директорию при необходимости."""
    path = tmp_path / "nested" / "dir" / "health.json"
    writer = SnapshotWriter(path=path, interval_sec=1)

    agg = HealthAggregator()
    writer.write(agg.snapshot(collector_state="running"))

    assert path.exists()


# ---------------------------------------------------------------
# Graceful shutdown hook (AC-HLT-05, AC-HLT-04 via CollectorApp later)
# ---------------------------------------------------------------
def test_health_aggregator_stop_is_safe() -> None:
    """Aggregator stop() безопасен (идемпотентен), без side-effects."""
    agg = HealthAggregator()
    agg.stop()
    agg.stop()  # второй вызов не падает

    # Ничего не падает — тест пройден.
    assert True