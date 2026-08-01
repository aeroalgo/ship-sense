from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from apps.edge.gateway.config import GatewaySettings
from apps.edge.gateway.modbus_filter.parser import extract_frames, parse_frame
from apps.edge.gateway.modbus_filter.policy import classify_frame, exception_response


class ModbusFilterGateway:
    def __init__(
        self,
        settings: GatewaySettings | None = None,
        *,
        log_path: Path | None = None,
    ) -> None:
        self.settings = settings or GatewaySettings.from_env()
        self.log_path = log_path or self.settings.log_path
        self._server: asyncio.AbstractServer | None = None

    def log_rejected(self, raw_frame: bytes, *, source_ip: str) -> None:
        frame = parse_frame(raw_frame)
        record = {
            "ts": datetime.now(UTC).isoformat(),
            "function_code": frame.function_code,
            "source_ip": source_ip,
            "raw_pdu_hash": hashlib.sha256(frame.pdu).hexdigest(),
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, separators=(",", ":")) + "\n")

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            self.settings.listen_host,
            self.settings.listen_port,
        )

    async def serve_forever(self) -> None:
        if self._server is None:
            await self.start()
        assert self._server is not None
        async with self._server:
            await self._server.serve_forever()

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        source = writer.get_extra_info("peername")
        source_ip = source[0] if source else "unknown"
        upstream_reader: asyncio.StreamReader | None = None
        upstream_writer: asyncio.StreamWriter | None = None
        try:
            buffer = b""
            while chunk := await reader.read(65536):
                buffer += chunk
                frames, buffer = extract_frames(buffer)
                for raw_frame in frames:
                    frame = parse_frame(raw_frame)
                    if not classify_frame(frame).allowed:
                        self.log_rejected(raw_frame, source_ip=source_ip)
                        writer.write(exception_response(frame))
                        await writer.drain()
                        continue
                    if upstream_writer is None:
                        upstream_reader, upstream_writer = await asyncio.open_connection(
                            self.settings.upstream_host,
                            self.settings.upstream_port,
                        )
                    upstream_writer.write(raw_frame)
                    await upstream_writer.drain()
                    assert upstream_reader is not None
                    response = await _read_frame(upstream_reader)
                    writer.write(response)
                    await writer.drain()
        finally:
            if upstream_writer is not None:
                upstream_writer.close()
                await upstream_writer.wait_closed()
            writer.close()
            await writer.wait_closed()


async def _read_frame(reader: asyncio.StreamReader) -> bytes:
    header = await reader.readexactly(6)
    length = int.from_bytes(header[4:6], "big")
    return header + await reader.readexactly(length)


async def run() -> None:
    gateway = ModbusFilterGateway()
    await gateway.serve_forever()


if __name__ == "__main__":
    asyncio.run(run())
