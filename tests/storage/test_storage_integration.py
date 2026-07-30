from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.edge.collector.src.collector.domain.models import Event, EventSeverity, Quality, TelemetrySample
from apps.edge.storage.events_repo import EventsRepo
from apps.edge.storage.writer import WriterService


def _sample(tag_id: str, ts: datetime) -> TelemetrySample:
    return TelemetrySample(
        tag_id=tag_id,
        value=12.5,
        unit="bar",
        source_ts=ts,
        edge_ts=ts + timedelta(milliseconds=5),
        quality=Quality.GOOD,
        source_id="integration",
    )


def _event(ts: datetime, *, tag_id: str | None = None) -> Event:
    return Event(
        event_name="integration.alarm",
        params={"tag_id": tag_id} if tag_id else {},
        ts=ts,
        edge_ts=ts,
        source="integration",
        tag_id=tag_id,
        severity=EventSeverity.WARNING,
        idempotency_key=f"integration-{uuid4()}",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_writer_end_to_end_preserves_sample_and_event_counts() -> None:
    samples_repo = AsyncMock()
    events_repo = AsyncMock()
    session = AsyncMock()
    samples_repo.insert_batch.return_value = 1000
    events_repo.insert_batch.return_value = 10
    service = WriterService(session=session, samples_repo=samples_repo, events_repo=events_repo)
    now = datetime.now(timezone.utc)

    messages = [_sample(f"TAG-{i % 20}", now + timedelta(seconds=i)) for i in range(1000)]
    messages.extend(_event(now + timedelta(seconds=i), tag_id=f"TAG-{i % 20}") for i in range(10))

    assert await service.flush_batches(messages) == 1010
    assert len(samples_repo.insert_batch.await_args.args[0]) == 1000
    assert len(events_repo.insert_batch.await_args.args[0]) == 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_correlation_returns_closest_sample() -> None:
    session = AsyncMock()
    event_id = uuid4()
    event_ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    event_row = MagicMock(
        event_id=event_id,
        idempotency_key="event-1",
        event_name="alarm",
        source="integration",
        source_ts=event_ts,
        edge_ts=event_ts,
        official_ts=event_ts,
        params={"tag_id": "TAG-1"},
        severity=1,
        reconstructed=False,
        ingested_at=event_ts,
    )
    before = MagicMock(
        tag_id="TAG-1", ts=event_ts - timedelta(milliseconds=80), value=1.0,
        quality=0, official_ts=event_ts - timedelta(milliseconds=80)
    )
    after = MagicMock(
        tag_id="TAG-1", ts=event_ts + timedelta(milliseconds=20), value=2.0,
        quality=0, official_ts=event_ts + timedelta(milliseconds=20)
    )
    results = [MagicMock(scalar_one_or_none=MagicMock(return_value=event_row)),
               MagicMock(scalar_one_or_none=MagicMock(return_value=before)),
               MagicMock(scalar_one_or_none=MagicMock(return_value=after))]
    session.execute.side_effect = results

    correlated = await EventsRepo(session).get_with_sample(event_id, window_ms=100)

    assert correlated.event.event_id == event_id
    assert correlated.sample is not None
    assert correlated.sample.value == 2.0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_quota_degrade_path_does_not_touch_events() -> None:
    from apps.edge.storage.quota_manager import DiskUsage, QuotaManager, QuotaSettings

    session = AsyncMock()
    manager = QuotaManager(session, settings=QuotaSettings(samples_quota_bytes=100))
    manager._disk_usage = AsyncMock(return_value=DiskUsage(1000, 100, 0))
    manager._samples_size = AsyncMock(return_value=250)
    manager._oldest_chunks = AsyncMock(return_value=[("chunk-1", 150)])
    manager._drop_chunk = AsyncMock()

    result = await manager.check_and_degrade()

    assert result.degraded_chunks == 1
    manager._drop_chunk.assert_awaited_once_with("chunk-1")
    sql = " ".join(str(call.args[0]) for call in session.execute.await_args_list).lower()
    assert "events" not in sql
