from __future__ import annotations

import asyncio

from app.events.models import Event
from app.telemetry.models import TelemetrySample


class QueueSink:
    """CanonicalSink поверх in-proc asyncio queues (ADR-COL-001).

    Ничего не шарит с api-процессом — очереди живут только в collector process.
    """

    def __init__(
        self,
        canonical: asyncio.Queue[TelemetrySample],
        events: asyncio.Queue[Event],
    ) -> None:
        self._canonical = canonical
        self._events = events

    async def write_sample(self, sample: TelemetrySample) -> None:
        await self._canonical.put(sample)

    async def write_event(self, event: Event) -> None:
        await self._events.put(event)

    @property
    def sample_depth(self) -> int:
        return self._canonical.qsize()

    @property
    def event_depth(self) -> int:
        return self._events.qsize()
