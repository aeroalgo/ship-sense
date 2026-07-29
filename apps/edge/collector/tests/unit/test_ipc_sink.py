from __future__ import annotations

import asyncio
import json
import struct
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import pytest

from collector.domain.models import Event, EventSeverity, Quality, TelemetrySample
from collector.sink.ipc_sink import IpcCanonicalSink, SinkUnavailable

# CanonicalSink (interfaces.py) — Protocol без @runtime_checkable;
# structural-check контрактных методов делаем напрямую, как в s05 suite.

UTC_NOW = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
LEN = struct.Struct(">I")  # 4-byte big-endian length prefix


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


async def _read_frame(reader: asyncio.StreamReader) -> dict | None:
    """Серверная сторона: один length-prefixed frame -> envelope dict."""
    header = await reader.readexactly(LEN.size)
    (length,) = LEN.unpack(header)
    if length == 0:
        return None
    raw = await reader.readexactly(length)
    return json.loads(raw.decode("utf-8"))


async def _close_writer(writer: asyncio.StreamWriter) -> None:
    writer.close()
    try:
        await writer.wait_closed()
    except (ConnectionResetError, BrokenPipeError, OSError):
        pass


@asynccontextmanager
async def _tcp_server(received: list[dict]) -> AsyncIterator[tuple[str, int]]:
    """Mock writer: localhost TCP, читает frames пока клиент не закроет writer."""

    async def _handle(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            while True:
                env = await _read_frame(reader)
                if env is None:
                    break
                received.append(env)
        except asyncio.IncompleteReadError:
            pass
        finally:
            await _close_writer(writer)

    server = await asyncio.start_server(_handle, host="127.0.0.1", port=0)
    port = server.sockets[0].getsockname()[1]
    try:
        yield ("127.0.0.1", port)
    finally:
        server.close()
        await server.wait_closed()


# ---------------------------------------------------------------
# Framing (length-prefixed JSON envelope) - AC-INT-01, стык T-002 §21.1
# ---------------------------------------------------------------
def test_round_trip_sample_and_event_over_tcp() -> None:
    """Mock writer читает frames; sample/event доходят бит-в-бит (round-trip)."""

    async def scenario() -> None:
        received: list[dict] = []
        async with _tcp_server(received) as (host, port):
            sink = IpcCanonicalSink(
                endpoint=(host, port),
                connect_attempts=3,
                retry_delay=0.0,
            )
            await sink.connect()
            sample = _telemetry()
            await sink.write_sample(sample)
            await sink.write_event(_event())
            await sink.flush()
            await sink.close()

        assert len(received) == 2
        assert received[0]["type"] == "sample"
        assert received[0]["payload"]["tag_id"] == sample.tag_id
        assert received[0]["payload"]["quality"] == sample.quality.value
        assert received[0]["payload"]["value"] == sample.value
        assert received[1]["type"] == "event"
        assert received[1]["payload"]["event_name"] == "source_up"
        assert received[1]["payload"]["idempotency_key"]  # non-empty

    asyncio.run(scenario())


def test_multiple_frames_in_one_connection() -> None:
    """Несколько frames в одном соединении - framing без delimiter ambiguity."""

    async def scenario() -> None:
        received: list[dict] = []
        async with _tcp_server(received) as (host, port):
            sink = IpcCanonicalSink((host, port), retry_delay=0.0)
            await sink.connect()
            for i in range(5):
                await sink.write_sample(_telemetry(value=i))
            await sink.flush()
            await sink.close()

        assert [r["type"] for r in received] == ["sample"] * 5
        assert [r["payload"]["value"] for r in received] == [0, 1, 2, 3, 4]

    asyncio.run(scenario())


def test_reconnect_after_server_drop() -> None:
    """Обрыв транспорта -> client переподключается, следующий write проходит."""

    async def scenario() -> None:
        received: list[dict] = []
        async with _tcp_server(received) as (host, port):
            sink = IpcCanonicalSink(
                (host, port),
                connect_attempts=5,
                retry_delay=0.0,
            )
            await sink.connect()
            await sink.write_sample(_telemetry(value=1))
            await sink.flush()
            await sink._drop_connection()  # имитация обрыва транспорта
            await sink.write_sample(_telemetry(value=2))
            await sink.flush()
            await sink.close()

        assert [r["payload"]["value"] for r in received] == [1, 2]

    asyncio.run(scenario())


def test_unavailable_raises_explicitly_not_silent() -> None:
    """Сервер отсутствует, попытки истекли -> SinkUnavailable, не silent drop."""

    async def scenario() -> None:
        sink = IpcCanonicalSink(
            ("127.0.0.1", 1),  # никто не слушает порт 1
            connect_attempts=2,
            retry_delay=0.0,
        )
        with pytest.raises(SinkUnavailable):
            await sink.connect()
        # Write без живого соединения обязан ругаться, а не глотать.
        with pytest.raises(SinkUnavailable):
            await sink.write_sample(_telemetry())

    asyncio.run(scenario())


def test_unix_socket_transport() -> None:
    """Unix socket framing - тот же envelope, файловый путь вместо host:port."""

    async def scenario() -> None:
        received: list[dict] = []
        with tempfile.TemporaryDirectory() as tmp:
            sock_path = str(Path(tmp) / "writer.sock")

            async def _handle(
                reader: asyncio.StreamReader,
                writer: asyncio.StreamWriter,
            ) -> None:
                try:
                    while True:
                        env = await _read_frame(reader)
                        if env is None:
                            break
                        received.append(env)
                except asyncio.IncompleteReadError:
                    pass
                finally:
                    await _close_writer(writer)

            server = await asyncio.start_unix_server(_handle, path=sock_path)
            try:
                sink = IpcCanonicalSink(endpoint=sock_path, retry_delay=0.0)
                await sink.connect()
                await sink.write_sample(_telemetry())
                await sink.flush()
                await sink.close()
            finally:
                server.close()
                await server.wait_closed()

        assert len(received) == 1
        assert received[0]["type"] == "sample"

    asyncio.run(scenario())


# ---------------------------------------------------------------
# Structural - CanonicalSink protocol (AC-INT-01)
# ---------------------------------------------------------------
def test_ipc_sink_satisfies_canonical_sink_protocol() -> None:
    """IpcCanonicalSink структурно соответствует CanonicalSink."""

    sink = IpcCanonicalSink(("127.0.0.1", 0), retry_delay=0.0)
    # Protocol без @runtime_checkable -> проверяем контрактные методы напрямую.
    assert callable(sink.write_sample)
    assert callable(sink.write_event)


def test_close_is_idempotent() -> None:
    """Двойной close - без исключения."""

    async def scenario() -> None:
        sink = IpcCanonicalSink(("127.0.0.1", 1), retry_delay=0.0)
        await sink.close()
        await sink.close()  # no exception

    asyncio.run(scenario())
