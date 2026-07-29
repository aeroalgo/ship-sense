from __future__ import annotations

import asyncio
import math
import struct
from collections.abc import Mapping
from typing import Any

from pymodbus.server import ModbusTcpServer
from pymodbus.simulator.simdata import DataType, SimData
from pymodbus.simulator.simdevice import SimDevice

from emulator.tag_model import TagGenerator

__all__ = ["ModbusServerAdapter"]


class ModbusServerAdapter:
    """Read-only Modbus TCP adapter backed by one tag snapshot provider."""

    def __init__(self, generator: TagGenerator | None = None) -> None:
        self._generator = generator
        self._server: ModbusTcpServer | None = None
        self._serve_task: asyncio.Task[None] | None = None
        self._tick_task: asyncio.Task[None] | None = None
        self.host = "127.0.0.1"
        self.port = 502
        self._tick = 0
        self._holding_start: int | None = None
        self._input_start: int | None = None

    @property
    def running(self) -> bool:
        return (
            self._server is not None
            and self._serve_task is not None
            and not self._serve_task.done()
        )

    def bind(self, generator: TagGenerator) -> None:
        """Bind the shared profile-driven snapshot provider."""
        if self.running:
            raise RuntimeError("cannot bind while server is running")
        self._generator = generator

    async def start(self, host: str = "127.0.0.1", port: int = 502) -> None:
        """Start a read-only TCP server and its 1 Hz snapshot ticker."""
        if self.running:
            return
        if self._generator is None:
            raise RuntimeError("TagGenerator is not bound")
        self.host = host
        self.port = port
        context = self._build_context(self._generator.tick(0))
        self._server = ModbusTcpServer(context, address=(host, port))
        self._serve_task = asyncio.create_task(
            self._server.serve_forever(),
            name="emulator-modbus-server",
        )
        while self._server.transport is None:
            await asyncio.sleep(0)
        socket = self._server.transport.sockets[0]
        self.port = int(socket.getsockname()[1])
        self._tick_task = asyncio.create_task(
            self._tick_loop(),
            name="emulator-modbus-ticker",
        )

    async def stop(self) -> None:
        """Stop server and ticker; safe to call repeatedly."""
        if self._tick_task is not None:
            self._tick_task.cancel()
            await asyncio.gather(self._tick_task, return_exceptions=True)
            self._tick_task = None
        if self._server is not None:
            await self._server.shutdown()
        if self._serve_task is not None:
            await asyncio.gather(self._serve_task, return_exceptions=True)
            self._serve_task = None
        self._server = None

    async def _tick_loop(self) -> None:
        while True:
            tick_hz = float(self._generator.profile.get("tick_hz", 1.0))
            await asyncio.sleep(1.0 / tick_hz)
            snapshot = self._generator.tick(self._tick + 1)
            self._update_snapshot(snapshot)
            self._tick += 1

    def _build_context(self, snapshot: Mapping[str, Any]) -> SimDevice:
        holding_image = _build_register_image(
            self._generator.profile["signals"],
            snapshot,
            holding=True,
        )
        input_image = _build_register_image(
            self._generator.profile["signals"],
            snapshot,
            holding=False,
        )
        holding: list[SimData] = []
        input_registers: list[SimData] = []
        self._holding_start = None
        self._input_start = None
        if holding_image is not None:
            start, values = holding_image
            self._holding_start = start
            holding.append(
                SimData(
                    address=start,
                    values=values,
                    datatype=DataType.REGISTERS,
                    readonly=True,
                )
            )
        if input_image is not None:
            start, values = input_image
            self._input_start = start
            input_registers.append(
                SimData(
                    address=start,
                    values=values,
                    datatype=DataType.REGISTERS,
                    readonly=True,
                )
            )
        empty_bits = [SimData(address=0, values=0, datatype=DataType.BITS)]
        return SimDevice(
            id=1,
            simdata=(
                empty_bits,
                empty_bits.copy(),
                holding,
                input_registers,
            ),
        )

    def _update_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        if self._server is None:
            return
        runtime = self._server.context.devices[1]
        for is_holding, block_key, block_start in (
            (True, "h", self._holding_start),
            (False, "i", self._input_start),
        ):
            if block_start is None:
                continue
            image = _build_register_image(
                self._generator.profile["signals"],
                snapshot,
                holding=is_holding,
            )
            if image is None:
                continue
            _start, values = image
            _block_start, _count, data, _flags = runtime.block[block_key]
            data[: len(values)] = values


def _build_register_image(
    signals: list[Mapping[str, Any]],
    snapshot: Mapping[str, Any],
    *,
    holding: bool,
) -> tuple[int, list[int]] | None:
    cells: dict[int, int] = {}
    for signal in signals:
        native_id = signal.get("native_ids", {}).get("modbus")
        if native_id is None:
            continue
        native_id = str(native_id)
        if holding != native_id.startswith("40"):
            continue
        address = _parse_address(native_id)
        registers = _encode_registers(
            snapshot.get(native_id, 0),
            signal.get("value_type", "float32"),
        )
        for offset, value in enumerate(registers):
            cells[address + offset] = value
    if not cells:
        return None
    start = min(cells)
    end = max(cells)
    return start, [cells.get(address, 0) for address in range(start, end + 1)]


def _parse_address(native_id: str) -> int:
    base = native_id.split(".", 1)[0]
    return int(base[2:]) if len(base) >= 3 else int(base)


def _encode_registers(value: Any, value_type: str) -> list[int]:
    if value_type == "float32":
        raw = struct.pack(">f", float(value))
        return [
            int.from_bytes(raw[index : index + 2], "big")
            for index in (0, 2)
        ]
    if value_type in {"int16", "uint16"}:
        number = int(value) & 0xFFFF
        return [number]
    if value_type in {"int32", "uint32"}:
        raw = int(value).to_bytes(4, "big", signed=value_type == "int32")
        return [
            int.from_bytes(raw[index : index + 2], "big")
            for index in (0, 2)
        ]
    if value_type == "boolean":
        return [1 if value else 0]
    if value_type == "string":
        encoded = str(value).encode("ascii", errors="ignore")
        if len(encoded) % 2:
            encoded += b"\x00"
        return [
            int.from_bytes(encoded[index : index + 2], "big")
            for index in range(0, len(encoded), 2)
        ] or [0]
    if isinstance(value, bool):
        return [1 if value else 0]
    if isinstance(value, (int, float)) and math.isfinite(value):
        return [int(value) & 0xFFFF]
    return [0]
