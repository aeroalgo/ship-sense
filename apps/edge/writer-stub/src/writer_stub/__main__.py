"""Writer stub (T-002 day-1) — drain-only framing server.

Length-prefixed framing по контракту collector → writer (README §framing):
``<4-byte BE length><UTF-8 JSON envelope>``.

Stub принимает frames, считает samples/events, пишет в лог samples/sec —
и больше ничего. Реальный writer (T-002) заменит этот модуль.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import struct
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("writer_stub")

_LEN = struct.Struct(">I")


class _Counters:
    def __init__(self) -> None:
        self.samples = 0
        self.events = 0
        self._window_start = time.monotonic()
        self._window_samples = 0

    def bump(self, kind: str) -> None:
        if kind == "sample":
            self.samples += 1
            self._window_samples += 1
        else:
            self.events += 1
        self._maybe_log()

    def _maybe_log(self) -> None:
        now = time.monotonic()
        elapsed = now - self._window_start
        if elapsed >= 5.0:
            rate = self._window_samples / elapsed
            logger.info(
                "samples/sec=%.1f total_samples=%d total_events=%d",
                rate,
                self.samples,
                self.events,
            )
            self._window_start = now
            self._window_samples = 0


async def _handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    counters: _Counters,
) -> None:
    peer = writer.get_extra_info("peername")
    logger.info("collector connected: %s", peer)
    try:
        while True:
            header = await reader.readexactly(4)
            (n,) = _LEN.unpack(header)
            body = await reader.readexactly(n)
            # body — JSON envelope {"type": ..., "payload": ...}; stub не парсит payload.
            kind = "event"
            if b'"sample"' in body:
                kind = "sample"
            counters.bump(kind)
    except asyncio.IncompleteReadError:
        logger.info("collector disconnected: %s", peer)
    except (ConnectionError, OSError) as exc:
        logger.warning("connection error from %s: %s", peer, exc)
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except (ConnectionError, OSError):
            pass


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ShipSense writer stub (T-002 day-1)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9009)
    args = parser.parse_args(argv)

    counters = _Counters()
    server = await asyncio.start_server(
        lambda r, w: _handle_client(r, w, counters),
        host=args.host,
        port=args.port,
    )
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    logger.info("writer stub listening on %s", addrs)

    async with server:
        await server.serve_forever()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
