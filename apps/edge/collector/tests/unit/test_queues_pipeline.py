from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

from collector.core.raw_consumer import RawConsumer
from collector.domain.interfaces import CanonicalSink
from collector.domain.models import (
    Event,
    EventSeverity,
    Quality,
    RawSample,
    TelemetrySample,
)
from collector.sink.mock_sink import MockSink
from collector.sink.null_sink import NullSink
from collector.sink.queue_sink import QueueSink


UTC_NOW = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)


def _raw(native_id: str = "40101", value: int = 1) -> RawSample:
    return RawSample(
        source_id="aps_main",
        native_id=native_id,
        raw_value=value,
        recv_ts=UTC_NOW,
    )


def _telemetry(native_id: str = "40101", value: int = 1) -> TelemetrySample:
    return TelemetrySample(
        tag_id=f"TAI_{native_id}",
        value=value,
        unit="unknown",
        source_ts=UTC_NOW,
        edge_ts=UTC_NOW,
        quality=Quality.GOOD,
        source_id="aps_main",
        native_id=native_id,
    )


def _event(name: str = "source_up") -> Event:
    return Event(
        event_name=name,
        ts=UTC_NOW,
        edge_ts=UTC_NOW,
        source="aps_main",
        severity=EventSeverity.INFO,
        idempotency_key=f"{name}:{UTC_NOW.isoformat()}",
    )


# ---------------------------------------------------------------
# Sinks (AC-INT-01, ADR-COL-001)
# ---------------------------------------------------------------
def test_mock_sink_counts_samples_and_events() -> None:
    """MockSink считает samples/events; счётчики доступны после put."""

    async def scenario() -> None:
        sink = MockSink()
        await sink.write_sample(_telemetry())
        await sink.write_event(_event())
        assert sink.samples == 1
        assert sink.events == 1
        assert sink.last_sample is not None
        assert sink.last_event is not None

    asyncio.run(scenario())


def test_null_sink_drops_silently() -> None:
    """NullSink drop без исключения."""

    async def scenario() -> None:
        sink = NullSink()
        await sink.write_sample(_telemetry())
        await sink.write_event(_event())

    asyncio.run(scenario())  # no exception = pass


def test_queue_sink_puts_sample_and_event_into_queues() -> None:
    """QueueSink кладёт sample в canonical, event в event queue; глубина растёт."""

    async def scenario() -> None:
        canonical: asyncio.Queue[TelemetrySample] = asyncio.Queue()
        events: asyncio.Queue[Event] = asyncio.Queue()
        sink = QueueSink(canonical=canonical, events=events)
        await sink.write_sample(_telemetry())
        await sink.write_event(_event())
        assert canonical.qsize() == 1
        assert events.qsize() == 1
        got_sample = canonical.get_nowait()
        got_event = events.get_nowait()
        assert got_sample.tag_id == "TAI_40101"  # noqa: E501
        assert got_event.event_name == "source_up"

    asyncio.run(scenario())


def test_queue_sink_exposes_depth() -> None:
    """queue_depth доступен без деструктивного get (health snapshot)."""

    async def scenario() -> None:
        canonical: asyncio.Queue[TelemetrySample] = asyncio.Queue()
        events: asyncio.Queue[Event] = asyncio.Queue()
        sink = QueueSink(canonical=canonical, events=events)
        assert sink.sample_depth == 0
        assert sink.event_depth == 0
        await sink.write_sample(_telemetry())
        await sink.write_sample(_telemetry())
        assert sink.sample_depth == 2

    asyncio.run(scenario())


def test_queue_sink_implements_canonical_sink_protocol() -> None:
    """QueueSink структурно соответствует CanonicalSink (T-001 contract).

    CanonicalSink — Protocol без @runtime_checkable, поэтому проверяем
    структурное соответствие (duck typing), не isinstance.
    """
    sink = QueueSink(canonical=asyncio.Queue(), events=asyncio.Queue())
    assert callable(getattr(sink, "write_sample", None))
    assert callable(getattr(sink, "write_event", None))


# ---------------------------------------------------------------
# RawConsumer — drain raw → sink (AC-HLT-03)
# ---------------------------------------------------------------
def test_raw_consumer_drains_raw_into_sink_via_passthrough() -> None:
    """RawConsumer drain: raw → passthrough normalizer → QueueSink.

    Burst из N put/gets не теряет данные; sample_depth == N.
    """

    async def scenario() -> None:
        canonical: asyncio.Queue[TelemetrySample] = asyncio.Queue()
        events: asyncio.Queue[Event] = asyncio.Queue()
        sink = QueueSink(canonical=canonical, events=events)
        raw: asyncio.Queue[RawSample] = asyncio.Queue()

        async def passthrough(sample: RawSample) -> TelemetrySample:
            return _telemetry(
                native_id=sample.native_id,
                value=int(sample.raw_value),
            )

        consumer = RawConsumer(raw_queue=raw, sink=sink, normalize=passthrough)
        consumer.start()

        n = 50
        for i in range(n):
            await raw.put(_raw(value=i))

        # Burst: сливаем батчами пока raw не опустеет (без потери).
        while not raw.empty():
            await consumer.drain_once(10)
        await consumer.stop()

        assert sink.sample_depth == n

    asyncio.run(scenario())


def test_raw_consumer_empty_queue_drains_nothing() -> None:
    """Пустая raw_queue → sink не получил ничего; exit без исключения."""

    async def scenario() -> None:
        sink = MockSink()
        raw: asyncio.Queue[RawSample] = asyncio.Queue()

        async def passthrough(sample: RawSample) -> TelemetrySample:
            return _telemetry()

        consumer = RawConsumer(raw_queue=raw, sink=sink, normalize=passthrough)
        consumer.start()
        drained = await consumer.drain_once(5)
        assert drained == 0
        assert sink.samples == 0
        await consumer.stop()

    asyncio.run(scenario())


def test_raw_consumer_raw_depth_exposed() -> None:
    """raw_queue depth доступен без get (health)."""

    async def scenario() -> None:
        raw: asyncio.Queue[RawSample] = asyncio.Queue()
        consumer = RawConsumer(
            raw_queue=raw,
            sink=NullSink(),
            normalize=_sync_normalize,
        )
        assert consumer.raw_depth == 0
        await raw.put(_raw())
        await raw.put(_raw())
        assert consumer.raw_depth == 2

    asyncio.run(scenario())


def test_raw_consumer_only_internal_queues_no_ipc() -> None:
    """Запрет: collector не шарит queues с api-процессом — только asyncio.Queue.

    In-proc only; нет Redis/Kafka/broker в зависимостях шага.
    """

    async def scenario() -> None:
        canonical: asyncio.Queue[TelemetrySample] = asyncio.Queue()
        events: asyncio.Queue[Event] = asyncio.Queue()
        raw: asyncio.Queue[RawSample] = asyncio.Queue()
        sink = QueueSink(canonical=canonical, events=events)
        consumer = RawConsumer(
            raw_queue=raw,
            sink=sink,
            normalize=_sync_normalize,
        )
        assert isinstance(consumer._raw_queue, asyncio.Queue)
        assert isinstance(sink._canonical, asyncio.Queue)
        assert isinstance(sink._events, asyncio.Queue)

    asyncio.run(scenario())


async def _sync_normalize(sample: RawSample) -> TelemetrySample:
    return _telemetry(native_id=sample.native_id, value=int(sample.raw_value))


# type alias docstring (not imported by runtime) — keeps Callable/Awaitable referenced.
_Normalizer = Callable[[RawSample], Awaitable[TelemetrySample]]
