from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from time import perf_counter

import pytest

from app.events.models import Event, EventSeverity
from app.telemetry.models import Quality, TelemetrySample
from apps.edge.storage.writer import WriterService


class CountingRepo:
    def __init__(self) -> None:
        self.items = 0

    async def insert_batch(self, items: list[object]) -> int:
        self.items += len(items)
        return len(items)


def _sample(index: int, now: datetime) -> TelemetrySample:
    ts = now + timedelta(milliseconds=index * 1000 / 586)
    return TelemetrySample(
        tag_id=f"TAG-{index % 586:03d}",
        value=float(index),
        unit="kPa",
        source_ts=ts,
        edge_ts=ts,
        quality=Quality.GOOD,
        source_id="load-test",
    )


def _event(index: int, now: datetime) -> Event:
    ts = now + timedelta(milliseconds=index * 500)
    return Event(
        event_name="load.event",
        params={"index": index},
        ts=ts,
        edge_ts=ts,
        source="load-test",
        severity=EventSeverity.INFO,
        idempotency_key=f"load-event-{index}",
    )


@pytest.mark.load
@pytest.mark.asyncio
async def test_writer_load_harness_586hz_has_no_queue_drops_and_fast_flushes() -> None:
    samples_repo = CountingRepo()
    events_repo = CountingRepo()
    session = CountingSession()
    service = WriterService(
        session=session,
        samples_repo=samples_repo,
        events_repo=events_repo,
        flush_interval_ms=100,
        max_batch_size=1000,
    )
    flush_durations: list[float] = []
    original_flush = service.flush_batches

    async def timed_flush(messages: list[object]) -> int:
        started = perf_counter()
        result = await original_flush(messages)  # type: ignore[arg-type]
        flush_durations.append((perf_counter() - started) * 1000)
        return result

    service.flush_batches = timed_flush  # type: ignore[method-assign]
    writer_task = asyncio.create_task(service.writer_loop())
    now = datetime.now(timezone.utc)

    for index in range(586):
        await service._queue.put(_sample(index, now))
    for index in range(2):
        await service._queue.put(_event(index, now))

    service._stopping = True
    await writer_task

    assert service._queue.qsize() == 0
    assert samples_repo.items == 586
    assert events_repo.items == 2
    assert session.notify_count >= 1
    assert flush_durations
    assert _percentile(flush_durations, 0.95) < 100


class CountingSession:
    def __init__(self) -> None:
        self.notify_count = 0

    async def execute(self, statement: object) -> None:
        if "NOTIFY" in str(statement):
            self.notify_count += 1


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * percentile))
    return ordered[index]
