"""L0 IPC framed → DB rows (T-002 s03).

WriterService (start_tcp + writer_loop) + real IpcCanonicalSink + DB session.
No mocks on SamplesRepo/EventsRepo.insert_batch.
Markers: integration + slow (Docker required).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from app.events.models import Event, EventSeverity
from app.telemetry.models import Quality, TelemetrySample
from apps.edge.collector.src.collector.sink.ipc_sink import IpcCanonicalSink

# Fixed UTC timestamp for determinism
UTC_TS = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)

# Poll timeout (wall clock for L0, session container already up)
POLL_TIMEOUT_S = 5.0
POLL_INTERVAL_S = 0.05


def _sample(tag_id: str = "TAI4101", value: float = 82.5) -> TelemetrySample:
    """Build a canonical sample with fixed ts."""
    return TelemetrySample(
        tag_id=tag_id,
        value=value,
        unit="unknown",
        source_ts=UTC_TS,
        edge_ts=UTC_TS,
        quality=Quality.GOOD,
        source_id="aps_main",
        native_id="40101",
    )


def _event(name: str = "source_up") -> Event:
    """Build a canonical event with idempotency_key."""
    return Event(
        event_name=name,
        params={},
        ts=UTC_TS,
        edge_ts=UTC_TS,
        source="aps_main",
        severity=EventSeverity.INFO,
        idempotency_key=f"{name}:{UTC_TS.isoformat()}",
        quality=Quality.GOOD,
    )


async def _poll_until(
    db_session,
    query: str,
    expected_min: int = 1,
    timeout_s: float = POLL_TIMEOUT_S,
    interval_s: float = POLL_INTERVAL_S,
) -> int:
    """Poll SELECT COUNT(*) until >= expected_min or timeout.

    Returns count on success. Raises AssertionError with message on timeout.
    """
    deadline = asyncio.get_event_loop().time() + timeout_s
    last_count = 0
    while True:
        result = await db_session.execute(text(query))
        count = result.scalar_one()
        last_count = int(count)
        if last_count >= expected_min:
            return last_count
        if asyncio.get_event_loop().time() >= deadline:
            raise AssertionError(
                f"timeout after {timeout_s}s: query={query!r} last_count={last_count} expected>={expected_min}"
            )
        await asyncio.sleep(interval_s)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_ipc_sample_persists_to_samples(writer_endpoint, db_session) -> None:
    """AC-PIPE-01: framed IPC sample → row in samples.

    Connect IpcCanonicalSink to writer_endpoint, write one sample, flush, poll DB.
    Assert tag_id, value≈82.5, quality=0 (GOOD).
    """
    host, port = writer_endpoint
    sink = IpcCanonicalSink(endpoint=(host, port), connect_attempts=5, retry_delay=0.05)
    await sink.connect()

    sample = _sample(tag_id="TAI4101", value=82.5)
    await sink.write_sample(sample)
    await sink.flush()
    await sink.close()

    # Poll until at least one row for this (tag_id, ts)
    count = await _poll_until(
        db_session,
        query="SELECT COUNT(*) FROM samples WHERE tag_id='TAI4101'",
        expected_min=1,
    )
    assert count >= 1

    # Verify value and quality via SQL (quality GOOD → 0)
    row = await db_session.execute(
        text(
            "SELECT value, quality FROM samples "
            "WHERE tag_id='TAI4101' AND ts=:ts ORDER BY ts DESC LIMIT 1"
        ),
        {"ts": UTC_TS},
    )
    value, quality = row.one()
    assert pytest.approx(value, abs=1e-6) == 82.5
    assert quality == 0  # GOOD


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_ipc_event_persists_to_events(writer_endpoint, db_session) -> None:
    """AC-PIPE-02: framed IPC event → row in events.

    Connect IpcCanonicalSink to writer_endpoint, write one event, flush, poll DB.
    Assert event_name and idempotency_key present (COUNT>=1).
    """
    host, port = writer_endpoint
    sink = IpcCanonicalSink(endpoint=(host, port), connect_attempts=5, retry_delay=0.05)
    await sink.connect()

    event = _event(name="source_up")
    await sink.write_event(event)
    await sink.flush()
    await sink.close()

    # Poll until at least one event row with this idempotency_key
    count = await _poll_until(
        db_session,
        query="SELECT COUNT(*) FROM events WHERE idempotency_key='source_up:2026-07-30T12:00:00+00:00'",
        expected_min=1,
    )
    assert count >= 1

    # Verify event_name via SQL
    row = await db_session.execute(
        text(
            "SELECT event_name FROM events "
            "WHERE idempotency_key='source_up:2026-07-30T12:00:00+00:00' LIMIT 1"
        )
    )
    event_name = row.scalar_one()
    assert event_name == "source_up"
