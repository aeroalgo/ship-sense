from datetime import datetime, timedelta, timezone

import pytest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from apps.edge.collector.src.collector.domain.models import Quality, TelemetrySample
from apps.edge.storage.samples_repo import SamplesRepo


def sample(*, tag_id: str, ts: datetime, quality: Quality = Quality.GOOD, value: float = 1.0) -> TelemetrySample:
    return TelemetrySample(
        tag_id=tag_id,
        value=value,
        unit="kPa",
        source_ts=ts,
        edge_ts=ts + timedelta(milliseconds=10),
        quality=quality,
        source_id="test",
    )


@pytest.mark.asyncio
async def test_insert_batch_deduplicates_quality_and_last_equal_wins():
    session = AsyncMock()
    repo = SamplesRepo(session)
    ts = datetime.now(timezone.utc)

    inserted = await repo.insert_batch(
        [
            sample(tag_id="T1", ts=ts, quality=Quality.BAD, value=1),
            sample(tag_id="T1", ts=ts, quality=Quality.GOOD, value=2),
            sample(tag_id="T1", ts=ts, quality=Quality.GOOD, value=3),
        ]
    )

    assert inserted == 1
    assert session.execute.await_count == 1
    assert session.commit.await_count == 1
    statement = session.execute.await_args.args[0]
    assert len(statement.compile().params) == 7


@pytest.mark.asyncio
async def test_query_trend_returns_bounded_points():
    session = AsyncMock()
    repo = SamplesRepo(session)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = MagicMock()
    result.scalars.return_value = [
        type("Row", (), {"tag_id": "T1", "ts": start, "value": 0, "quality": 0, "official_ts": start})(),
        type("Row", (), {"tag_id": "T1", "ts": start + timedelta(minutes=1), "value": 1, "quality": 0, "official_ts": start})(),
        type("Row", (), {"tag_id": "T1", "ts": start + timedelta(minutes=2), "value": 2, "quality": 0, "official_ts": start})(),
    ]
    session.execute.return_value = result

    points = await repo.query_trend("T1", start, start + timedelta(hours=1), max_points=3)

    assert [point.value for point in points] == [0, 1, 2]
