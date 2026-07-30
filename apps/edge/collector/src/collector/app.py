"""CollectorApp — orchestration skeleton (AC-HLT-04, AC-HLT-05).

L2 scope: wire sources + consumer + health + graceful shutdown.
Not a full runtime — normalizer stub, no real plugins loaded.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
from collections.abc import Awaitable, Callable
from pathlib import Path

from collector.core.raw_consumer import RawConsumer
from collector.domain.interfaces import CanonicalSink, SourceConnector
from collector.domain.raw_models import RawSample
from app.telemetry.models import TelemetrySample
from collector.health.aggregator import HealthAggregator
from collector.health.snapshot_writer import SnapshotWriter

logger = logging.getLogger(__name__)

# Type alias for passthrough normalizer (hook for B4)
Normalizer = Callable[[RawSample], Awaitable[object] | object]


async def _write_snapshot(
    writer: SnapshotWriter,
    health: HealthAggregator,
    supervisors: list,
    collector_state: str,
) -> None:
    for supervisor in supervisors:
        status = await supervisor.healthcheck()
        health.update_source(status)
    writer.write(health.snapshot(collector_state=collector_state))


async def _snapshot_for(
    health: HealthAggregator,
    supervisors: list,
    collector_state: str,
):
    for supervisor in supervisors:
        health.update_source(await supervisor.healthcheck())
    return health.snapshot(collector_state=collector_state)


class CollectorApp:
    """Оркестратор collector (edge).

    Lifecycle:
      - start(): запустить consumer + sources (supervisors)
      - stop(): cancel consumer, stop sources (graceful), flush health
      - SIGTERM → exit 0 (AC-HLT-05)

    Dependencies (injected):
      - raw_queue: asyncio.Queue[RawSample]
      - sink: CanonicalSink (QueueSink / IpcCanonicalSink / MockSink)
      - normalize: async callable RawSample → TelemetrySample
      - sources: list[SourceConnector] (уже созданные плагины)
      - supervisors: list[SourceSupervisor] (обёртки над sources)
      - health: HealthAggregator
      - snapshot_writer: SnapshotWriter (опционально)

    В этом шаге (s14) — skeleton: wiring + shutdown contract.
    Полная интеграция (s06+) и реальные плагины (s07–s10) подставят продьюсеров.
    """

    def __init__(
        self,
        *,
        raw_queue: asyncio.Queue[RawSample],
        sink: CanonicalSink,
        normalize: Normalizer,
        sources: list[SourceConnector],
        supervisors: list,  # SourceSupervisor — избегаем циклического импорта
        health: HealthAggregator,
        snapshot_writer: SnapshotWriter | None = None,
    ) -> None:
        self._raw_queue = raw_queue
        self._sink = sink
        self._normalize = normalize
        self._sources = sources
        self._supervisors = supervisors
        self._health = health
        self._snapshot_writer = snapshot_writer

        self._consumer = RawConsumer(raw_queue=raw_queue, sink=sink, normalize=normalize)
        self._stopped = False
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        """Запустить consumer + все supervisors."""
        if self._stopped:
            return

        # Consumer
        self._consumer.start()

        # Sources (supervisors)
        for sup in self._supervisors:
            await sup.start()

        if self._snapshot_writer is not None:
            await self._snapshot_writer.start(
                lambda: _snapshot_for(
                    self._health, self._supervisors, "running"
                )
            )

        logger.info(
            "collector started: sources=%d", len(self._supervisors)
        )

    async def stop(self) -> None:
        """Graceful stop: consumer → sources → health flush (AC-HLT-04)."""
        if self._stopped:
            return
        self._stopped = True
        self._stop_event.set()

        # 1) Остановить consumer (дренаж in-proc)
        await self._consumer.stop()

        # 2) Остановить supervisors (cancel + disconnect)
        for sup in self._supervisors:
            with contextlib.suppress(Exception):
                await sup.stop()

        # 3) Health flush
        if self._snapshot_writer is not None:
            with contextlib.suppress(Exception):
                await self._snapshot_writer.stop()
                snap = await _snapshot_for(
                    self._health, self._supervisors, "stopped"
                )
                self._snapshot_writer.write(snap)

        logger.info("collector stopped cleanly")

    async def run_until_stopped(self) -> None:
        """Блокирующий рантайм: ждёт stop_event (SIGTERM / ручной stop)."""
        await self._stop_event.wait()

    def request_stop(self) -> None:
        """Синхронный триггер остановки (из signal handler)."""
        self._stop_event.set()


async def _passthrough_normalize(sample: RawSample) -> TelemetrySample:
    """Заглушка нормализатора до B4 (s13). Пробрасывает raw как telemetry (dev only)."""
    # Минимальный маппинг; реальная нормализация (quality, unit, events) — в s11/s13.
    return TelemetrySample(
        tag_id=sample.native_id,
        value=sample.raw_value if isinstance(sample.raw_value, (int, float, str, bool)) else None,
        unit="unknown",
        source_ts=sample.source_ts or sample.recv_ts,
        edge_ts=sample.recv_ts,
        quality=Quality.GOOD,
        source_id=sample.source_id,
        native_id=sample.native_id,
    )


def build_collector_app(
    *,
    raw_queue: asyncio.Queue[RawSample],
    sink: CanonicalSink,
    sources: list[SourceConnector],
    supervisors: list,
    health: HealthAggregator,
    snapshot_path: Path | None = None,
    normalize: Normalizer | None = None,
) -> CollectorApp:
    """Фабрика CollectorApp с совместимым passthrough default."""
    writer = (
        SnapshotWriter(path=snapshot_path, interval_sec=5)
        if snapshot_path
        else None
    )
    return CollectorApp(
        raw_queue=raw_queue,
        sink=sink,
        normalize=normalize or _passthrough_normalize,
        sources=sources,
        supervisors=supervisors,
        health=health,
        snapshot_writer=writer,
    )


def install_signal_handlers(app: CollectorApp) -> None:
    """SIGTERM/SIGINT → request_stop (AC-HLT-05)."""

    def _handler(signum: int, frame: object) -> None:  # noqa: ARG001
        logger.info("signal %s received — requesting stop", signum)
        app.request_stop()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):  # Windows
            loop.add_signal_handler(sig, lambda s=sig: _handler(s, None))
