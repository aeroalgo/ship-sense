from __future__ import annotations

import asyncio
import json
import struct
from typing import TYPE_CHECKING

from collector.domain.models import Event, TelemetrySample

if TYPE_CHECKING:
    from os import PathLike

# Length-prefixed framing: 4-byte big-endian unsigned length + UTF-8 JSON body.
# Binary-safe: никакого delimiter-ambiguity, как у NDJSON.
_LEN = struct.Struct(">I")


class SinkUnavailable(RuntimeError):
    """IPC sink не смог подключиться/переподключиться к writer (T-002).

    Явная ошибка вместо silent drop данных — политикой ADR-COL-001 / §21.1
    collector обязан сигнализировать потерю стыка, а не глотать samples.
    """


class IpcCanonicalSink:
    """CanonicalSink поверх IPC framing к процессу writer (T-002 §21.1).

    Транспорт выбирается по типу endpoint:
      - ``str`` / ``PathLike`` -> Unix domain socket (файл).
      - ``(host, port)`` tuple  -> localhost TCP.

    Framing wire-контракт (см. README):
      ``<4-byte BE length><UTF-8 JSON envelope>`` где envelope
      ``{"type": "sample" | "event", "payload": {...}}``.

    Потеря связи -> bounded reconnect; при истечении попыток -> SinkUnavailable.
    """

    def __init__(
        self,
        endpoint: str | PathLike[str] | tuple[str, int],
        *,
        connect_attempts: int = 5,
        retry_delay: float = 0.2,
    ) -> None:
        self._endpoint = endpoint
        self._connect_attempts = max(1, connect_attempts)
        self._retry_delay = retry_delay
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    # ----- CanonicalSink protocol (AC-INT-01) --------------------------
    async def write_sample(self, sample: TelemetrySample) -> None:
        await self._send("sample", sample.model_dump(mode="json"))

    async def write_event(self, event: Event) -> None:
        await self._send("event", event.model_dump(mode="json"))

    # ----- connection lifecycle ----------------------------------------
    async def connect(self) -> None:
        async with self._lock:
            await self._connect_with_retries()

    async def flush(self) -> None:
        """Дождаться отправки буфера транспорта (drain)."""
        async with self._lock:
            if self._writer is None:
                raise SinkUnavailable("sink not connected")
            await self._writer.drain()

    async def close(self) -> None:
        """Idempotent закрытие транспорта."""
        async with self._lock:
            await self._close_unchecked()

    async def _drop_connection(self) -> None:
        """Test hook: имитация обрыва транспорта без переподключения."""
        async with self._lock:
            await self._close_unchecked()

    # ----- internals ---------------------------------------------------
    async def _send(self, msg_type: str, payload: dict) -> None:
        body = json.dumps({"type": msg_type, "payload": payload}).encode("utf-8")
        frame = _LEN.pack(len(body)) + body
        async with self._lock:
            await self._send_locked(frame, msg_type)

    async def _send_locked(self, frame: bytes, msg_type: str) -> None:
        # Первая попытка; при dead/обрыве -> reconnect + ровно один retry.
        if self._writer is None:
            await self._connect_with_retries()
        try:
            assert self._writer is not None  # narrowed by _connect_with_retries
            self._writer.write(frame)
            await self._writer.drain()
            return
        except (ConnectionError, OSError, asyncio.CancelledError) as exc:
            if isinstance(exc, asyncio.CancelledError):
                raise
            await self._close_unchecked()
            await self._connect_with_retries()
            assert self._writer is not None
            self._writer.write(frame)
            await self._writer.drain()

    async def _connect_with_retries(self) -> None:
        last_exc: Exception | None = None
        for attempt in range(self._connect_attempts):
            try:
                self._reader, self._writer = await self._open()
                return
            except OSError as exc:
                last_exc = exc
                if self._retry_delay:
                    await asyncio.sleep(self._retry_delay)
        raise SinkUnavailable(
            f"cannot connect to writer at {self._endpoint!r}: {last_exc}"
        )

    async def _open(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        if isinstance(self._endpoint, tuple):
            host, port = self._endpoint
            return await asyncio.open_connection(host, port)
        return await asyncio.open_unix_connection(str(self._endpoint))

    async def _close_unchecked(self) -> None:
        writer = self._writer
        self._reader = None
        self._writer = None
        if writer is None:
            return
        writer.close()
        try:
            await writer.wait_closed()
        except (ConnectionError, BrokenPipeError, OSError):
            pass
