from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from apps.edge.collector.src.collector.domain.models import Event, EventSeverity, Quality, TelemetrySample
from apps.edge.storage.writer import WriterService


def sample() -> TelemetrySample:
    now = datetime.now(timezone.utc)
    return TelemetrySample(
        tag_id="T-1", value=1.0, unit="bar", source_ts=now,
        edge_ts=now, quality=Quality.GOOD, source_id="test",
    )


def event() -> Event:
    now = datetime.now(timezone.utc)
    return Event(
        event_name="test.event", params={}, ts=now, edge_ts=now,
        source="test", tag_id=None, severity=EventSeverity.INFO,
        idempotency_key="event-1", quality=Quality.GOOD,
    )


@pytest.mark.asyncio
async def test_flush_batches_partitions_samples_events_and_notifies():
    samples_repo = AsyncMock()
    events_repo = AsyncMock()
    samples_repo.insert_batch.return_value = 1
    events_repo.insert_batch.return_value = 1
    session = AsyncMock()
    service = WriterService(session=session, samples_repo=samples_repo, events_repo=events_repo)

    flushed = await service.flush_batches([sample(), event()])

    assert flushed == 2
    samples_repo.insert_batch.assert_awaited_once()
    events_repo.insert_batch.assert_awaited_once()
    session.execute.assert_awaited_once()
    assert "shipsense_live" in str(session.execute.await_args.args[0])


@pytest.mark.asyncio
async def test_flush_batches_deduplicates_samples_by_tag_and_timestamp():
    samples_repo = AsyncMock()
    events_repo = AsyncMock()
    session = AsyncMock()
    service = WriterService(session=session, samples_repo=samples_repo, events_repo=events_repo)
    first = sample()
    duplicate = first.model_copy(update={"value": 2.0})

    await service.flush_batches([first, duplicate])

    batch = samples_repo.insert_batch.await_args.args[0]
    assert len(batch) == 1
