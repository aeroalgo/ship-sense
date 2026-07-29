from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, MagicMock

from apps.edge.collector.src.collector.domain.models import Event as DomainEvent, EventSeverity, Quality
from apps.edge.storage.events_repo import EventsRepo, EventFilters, EventRow
from apps.edge.storage.schemas import Event as DBEvent, Sample as DBSample


def domain_event(
    *,
    idempotency_key: str,
    event_name: str = "test.event",
    source: str = "test",
    ts: datetime | None = None,
    tag_id: str | None = None,
    severity: EventSeverity = EventSeverity.INFO,
) -> DomainEvent:
    if ts is None:
        ts = datetime.now(timezone.utc)
    return DomainEvent(
        event_name=event_name,
        params={"foo": "bar"},
        ts=ts,
        edge_ts=ts + timedelta(milliseconds=5),
        source=source,
        tag_id=tag_id,
        severity=severity,
        idempotency_key=idempotency_key,
        quality=Quality.GOOD,
    )


@pytest.mark.asyncio
async def test_insert_batch_deduplicates_by_idempotency_key():
    session = AsyncMock()
    repo = EventsRepo(session)
    ts = datetime.now(timezone.utc)

    events = [
        domain_event(idempotency_key="key1", ts=ts, event_name="event1"),
        domain_event(idempotency_key="key2", ts=ts, event_name="event2"),
        domain_event(idempotency_key="key1", ts=ts, event_name="event1_updated"),
    ]

    session.execute.return_value.rowcount = 2
    inserted = await repo.insert_batch(events)

    assert inserted == 2
    assert session.execute.await_count == 1
    assert session.commit.await_count == 1


@pytest.mark.asyncio
async def test_query_journal_returns_rows_with_filters():
    session = AsyncMock()
    repo = EventsRepo(session)

    filters = EventFilters(
        ts_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ts_to=datetime(2026, 1, 2, tzinfo=timezone.utc),
        event_name="test.event",
        source="sensor1",
        tag_id="tag123",
        lifecycle="active",
        ack_state="acked",
    )

    db_event = DBEvent(
        event_id=uuid4(),
        idempotency_key="key1",
        event_name="test.event",
        source="sensor1",
        source_ts=filters.ts_from,
        edge_ts=filters.ts_from,
        official_ts=filters.ts_from,
        params={"tag_id": "tag123", "lifecycle": "active", "ack_state": "acked"},
        severity=0,
        reconstructed=False,
        ingested_at=filters.ts_from,
    )

    result = MagicMock()
    result.scalars.return_value.all.return_value = [db_event]
    session.execute.return_value = result

    rows = await repo.query_journal(filters, limit=10, offset=5)

    assert len(rows) == 1
    assert rows[0].idempotency_key == "key1"
    assert session.execute.await_count == 1


@pytest.mark.asyncio
async def test_get_with_sample_no_tag_returns_event_only():
    session = AsyncMock()
    repo = EventsRepo(session)
    event_id = uuid4()
    now_ts = datetime.now(timezone.utc)

    db_event = DBEvent(
        event_id=event_id,
        idempotency_key="key1",
        event_name="test.event",
        source="sensor1",
        source_ts=now_ts,
        edge_ts=now_ts,
        official_ts=now_ts,
        params={},
        severity=0,
        reconstructed=False,
        ingested_at=now_ts,
    )

    event_result = MagicMock()
    event_result.scalar_one_or_none.return_value = db_event
    session.execute.return_value = event_result

    res = await repo.get_with_sample(event_id, window_ms=100)

    assert res.event.event_id == event_id
    assert res.sample is None
    assert session.execute.await_count == 1


@pytest.mark.asyncio
async def test_get_with_sample_correlation_selects_closest():
    session = AsyncMock()
    repo = EventsRepo(session)
    event_id = uuid4()
    event_ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    db_event = DBEvent(
        event_id=event_id,
        idempotency_key="key1",
        event_name="test.event",
        source="sensor1",
        source_ts=event_ts,
        edge_ts=event_ts,
        official_ts=event_ts,
        params={"tag_id": "tag1"},
        severity=0,
        reconstructed=False,
        ingested_at=event_ts,
    )

    event_result = MagicMock()
    event_result.scalar_one_or_none.return_value = db_event

    sample_before = DBSample(
        tag_id="tag1",
        ts=event_ts - timedelta(milliseconds=50),
        value=10.0,
        quality=0,
        source_ts=event_ts - timedelta(milliseconds=50),
        edge_ts=event_ts - timedelta(milliseconds=50),
        official_ts=event_ts - timedelta(milliseconds=50),
    )

    sample_after = DBSample(
        tag_id="tag1",
        ts=event_ts + timedelta(milliseconds=10),
        value=20.0,
        quality=0,
        source_ts=event_ts + timedelta(milliseconds=10),
        edge_ts=event_ts + timedelta(milliseconds=10),
        official_ts=event_ts + timedelta(milliseconds=10),
    )

    result_before = MagicMock()
    result_before.scalar_one_or_none.return_value = sample_before

    result_after = MagicMock()
    result_after.scalar_one_or_none.return_value = sample_after

    session.execute.side_effect = [event_result, result_before, result_after]

    res = await repo.get_with_sample(event_id, window_ms=100)

    assert res.event.event_id == event_id
    assert res.sample is not None
    assert res.sample.value == 20.0
    assert session.execute.await_count == 3
