from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
from collections.abc import Awaitable, Callable

from collector.domain.interfaces import CanonicalSink
from collector.domain.models import Event, RawSample, TelemetrySample


NormalizerResult = (
    TelemetrySample | tuple[TelemetrySample, list[Event]] | None
)
Normalizer = Callable[
    [RawSample], Awaitable[NormalizerResult] | NormalizerResult
]

logger = logging.getLogger(__name__)


class RawConsumer:
    """Drain raw_queue → normalizer hook → CanonicalSink (ADR-COL-001).

    In-proc bridge: raw (source producers) → passthrough normalizer stub →
    canonical/event queues. Никакого IPC в этом шаге — queue не шарится
    с api-процессом.
    """

    def __init__(
        self,
        raw_queue: asyncio.Queue[RawSample],
        sink: CanonicalSink,
        normalize: Normalizer,
    ) -> None:
        self._raw_queue = raw_queue
        self._sink = sink
        self._normalize = normalize
        self._task: asyncio.Task[None] | None = None

    @property
    def raw_depth(self) -> int:
        return self._raw_queue.qsize()

    def start(self) -> None:
        """Background drain loop (cancel-friendly)."""
        if self._task is None:
            self._task = asyncio.create_task(
                self._loop(), name="raw_consumer:drain"
            )

    async def drain_once(self, batch: int) -> int:
        """Слить до ``batch`` samples синхронно и вернуть число обработанных."""
        processed = 0
        for _ in range(batch):
            if self._raw_queue.empty():
                break
            sample = self._raw_queue.get_nowait()
            result = self._normalize(sample)
            if inspect.isawaitable(result):
                result = await result
            await self._write_result(result)
            processed += 1

        return processed

    async def _loop(self) -> None:
        try:
            while True:
                sample = await self._raw_queue.get()
                result = self._normalize(sample)
                if inspect.isawaitable(result):
                    result = await result
                await self._write_result(result)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("raw_consumer drain loop exited unexpectedly")

    async def _write_result(self, result: NormalizerResult) -> None:
        if result is None:
            return
        if isinstance(result, tuple):
            sample, events = result
        else:
            sample, events = result, []
        await self._sink.write_sample(sample)
        for event in events:
            await self._sink.write_event(event)

    async def stop(self) -> None:
        if self._task is not None and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self._task = None
