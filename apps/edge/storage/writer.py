from __future__ import annotations

import asyncio
import json
import struct
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.models import Event
from app.telemetry.models import Quality, TelemetrySample
from apps.edge.storage.events_repo import EventsRepo
from apps.edge.storage.samples_repo import SamplesRepo


_HEADER = struct.Struct(">I")
Message = TelemetrySample | Event


def _deduplicate(messages: list[Message]) -> list[Message]:
    result: dict[tuple[str, Any], Message] = {}
    events: dict[str, Event] = {}
    for message in messages:
        if isinstance(message, Event):
            events[message.idempotency_key] = message
        else:
            result[(message.tag_id, message.source_ts)] = message
    return [*result.values(), *events.values()]


class WriterService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        samples_repo: SamplesRepo,
        events_repo: EventsRepo,
        flush_interval_ms: int = 100,
        max_batch_size: int = 5000,
        socket_path: str | None = None,
        quarantined_tags: Callable[[], frozenset[str]] | None = None,
    ) -> None:
        self.session = session
        self.samples_repo = samples_repo
        self.events_repo = events_repo
        self.flush_interval = flush_interval_ms / 1000
        self.max_batch_size = max_batch_size
        self.socket_path = socket_path
        self.quarantined_tags = quarantined_tags
        self._queue: asyncio.Queue[Message] = asyncio.Queue(maxsize=max_batch_size * 2)
        self._stopping = False
        self._server: asyncio.AbstractServer | None = None

    async def flush_batches(self, messages: list[Message]) -> int:
        messages = _deduplicate(messages)
        samples = [item for item in messages if isinstance(item, TelemetrySample)]
        events = [item for item in messages if isinstance(item, Event)]

        # Dual-path: force quality=4 for quarantined tags (override good/uncertain/stale, not bad)
        if samples and self.quarantined_tags is not None:
            qset = self.quarantined_tags()
            for i, s in enumerate(samples):
                if s.tag_id in qset and s.quality not in (Quality.BAD, Quality.QUARANTINE):
                    samples[i] = s.model_copy(update={"quality": Quality.QUARANTINE})

        inserted = 0
        if samples:
            inserted += await self.samples_repo.insert_batch(samples)
        if events:
            inserted += await self.events_repo.insert_batch(events)
        if messages:
            await self.session.execute(text("NOTIFY shipsense_live, 'batch'"))
        return inserted

    async def run(self) -> None:
        if self.socket_path is None:
            raise ValueError("socket_path is required")
        self._server = await asyncio.start_unix_server(self._handle_client, self.socket_path)
        try:
            await self.writer_loop()
        finally:
            await self.shutdown()

    async def start_tcp(self, host: str = "0.0.0.0", port: int = 0) -> tuple[str, int]:
        """Start TCP server and return the bound (host, port).

        If port=0, OS assigns an ephemeral port. Raises RuntimeError with
        explicit message if no sockets after start_server (defensive).
        """
        self._server = await asyncio.start_server(self._handle_client, host, port)
        sockets = getattr(self._server, "sockets", None) or []
        if not sockets:
            raise RuntimeError("writer TCP server has no sockets")
        sockname = sockets[0].getsockname()
        if isinstance(sockname, (list, tuple)) and len(sockname) >= 2:
            bound_host = str(sockname[0])
            bound_port = int(sockname[1])
        else:
            bound_host = str(sockname)
            bound_port = 0
        return bound_host, bound_port

    async def run_tcp(self, host: str = "0.0.0.0", port: int = 9009) -> None:
        """Run TCP server by delegating to start_tcp + writer_loop + shutdown.

        API and behavior for __main__.py callers unchanged (default port 9009).
        """
        await self.start_tcp(host, port)
        try:
            await self.writer_loop()
        finally:
            await self.shutdown()

    async def writer_loop(self) -> None:
        batch: list[Message] = []
        while not self._stopping or not self._queue.empty():
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=self.flush_interval)
                batch.append(item)
                if len(batch) >= self.max_batch_size:
                    await self.flush_batches(batch)
                    batch.clear()
            except asyncio.TimeoutError:
                if batch:
                    await self.flush_batches(batch)
                    batch.clear()
        if batch:
            await self.flush_batches(batch)

    async def shutdown(self, timeout: float = 30.0) -> None:
        self._stopping = True
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while not self._stopping:
                header = await reader.readexactly(_HEADER.size)
                size = _HEADER.unpack(header)[0]
                payload = json.loads((await reader.readexactly(size)).decode())
                model = Event if payload["type"] == "event" else TelemetrySample
                await self._queue.put(model.model_validate(payload["payload"]))
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()


async def writer_loop(queue: asyncio.Queue[Message], service: WriterService) -> None:
    service._queue = queue
    await service.writer_loop()


async def flush_batches(service: WriterService, messages: list[Message]) -> int:
    return await service.flush_batches(messages)
