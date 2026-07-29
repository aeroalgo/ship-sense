import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from apps.edge.storage.time_axis import TimeAxisService, ClockShift, OfficialDateTime


def test_compute_official_ts_prefer_source():
    service = TimeAxisService(prefer_source_ts=True, max_skew_sec=60)
    source_ts = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
    edge_ts = datetime(2026, 7, 29, 12, 0, 10, tzinfo=timezone.utc)

    # Valid case
    res = service.compute_official_ts(source_ts, edge_ts, "good")
    assert res == source_ts
    assert res.quality == "good"

    # Bad year (< 2000)
    bad_year_ts = datetime(1999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    res = service.compute_official_ts(bad_year_ts, edge_ts, "good")
    assert res == edge_ts
    assert res.quality == "time_bad"

    # Bad year (> 2100)
    bad_year_ts2 = datetime(2101, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    res = service.compute_official_ts(bad_year_ts2, edge_ts, "good")
    assert res == edge_ts
    assert res.quality == "time_bad"

    # Max skew exceeded
    skewed_source_ts = datetime(2026, 7, 29, 12, 5, 0, tzinfo=timezone.utc)
    res = service.compute_official_ts(skewed_source_ts, edge_ts, "good")
    assert res == edge_ts
    assert res.quality == "time_bad"

    # Quality bad
    res = service.compute_official_ts(source_ts, edge_ts, "bad")
    assert res == edge_ts
    assert res.quality == "time_bad"


def test_compute_official_ts_prefer_edge():
    service = TimeAxisService(prefer_source_ts=False)
    source_ts = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
    edge_ts = datetime(2026, 7, 29, 12, 0, 10, tzinfo=timezone.utc)

    res = service.compute_official_ts(source_ts, edge_ts, "good")
    assert res == edge_ts
    assert res.quality == "good"


def test_detect_clock_shift():
    service = TimeAxisService(backward_jump_sec=60, forward_jump_sec=300)
    prev = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)

    # Normal step
    assert service.detect_clock_shift(prev, prev + timedelta(seconds=10)) is None

    # Backward jump > 60s
    shift_back = service.detect_clock_shift(prev, prev - timedelta(seconds=61))
    assert shift_back is not None
    assert shift_back.detected_on == "edge"
    assert shift_back.delta == timedelta(seconds=-61)
    assert shift_back.prev_ts == prev
    assert shift_back.new_ts == prev - timedelta(seconds=61)

    # Forward jump > 300s
    shift_fwd = service.detect_clock_shift(prev, prev + timedelta(seconds=301))
    assert shift_fwd is not None
    assert shift_fwd.detected_on == "edge"
    assert shift_fwd.delta == timedelta(seconds=301)


@pytest.mark.asyncio
async def test_record_clock_shift():
    # Mock EventsRepo and session
    session_mock = AsyncMock()
    events_repo_mock = MagicMock()
    events_repo_mock._session = session_mock

    # Mock select result to return None, and insert result to have rowcount = 1
    select_result = MagicMock()
    select_result.scalar_one_or_none.return_value = None

    insert_result = MagicMock()
    insert_result.rowcount = 1

    session_mock.execute.side_effect = [select_result, insert_result, MagicMock()]

    service = TimeAxisService()
    shift = ClockShift(
        detected_on="edge",
        delta=timedelta(seconds=-70),
        prev_ts=datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc),
        new_ts=datetime(2026, 7, 29, 11, 58, 50, tzinfo=timezone.utc),
    )

    await service.record_clock_shift(shift, events_repo_mock)

    # Verify that session.execute was called for SELECT, INSERT event, and INSERT log
    assert session_mock.execute.call_count == 3
    session_mock.commit.assert_called_once()


@pytest.mark.asyncio
async def test_record_clock_shift_duplicate():
    # Mock EventsRepo and session
    session_mock = AsyncMock()
    events_repo_mock = MagicMock()
    events_repo_mock._session = session_mock

    # Mock select result to return a mock event_id (meaning event exists)
    select_result = MagicMock()
    import uuid
    select_result.scalar_one_or_none.return_value = uuid.uuid4()

    session_mock.execute.return_value = select_result

    service = TimeAxisService()
    shift = ClockShift(
        detected_on="edge",
        delta=timedelta(seconds=-70),
        prev_ts=datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc),
        new_ts=datetime(2026, 7, 29, 11, 58, 50, tzinfo=timezone.utc),
    )

    await service.record_clock_shift(shift, events_repo_mock)

    # Verify that only SELECT was executed, and no commit
    assert session_mock.execute.call_count == 1
    session_mock.commit.assert_not_called()
