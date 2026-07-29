from __future__ import annotations

import asyncio
import socket
from collections.abc import Mapping
from typing import Any

from asyncua import Server, ua

from emulator.tag_model import TagGenerator

__all__ = ["OpcUaServerAdapter"]


class OpcUaServerAdapter:
    """Read-only OPC UA adapter backed by one tag snapshot provider."""

    def __init__(self, generator: TagGenerator | None = None) -> None:
        self._generator = generator
        self._server: Server | None = None
        self._serve_task: asyncio.Task[None] | None = None
        self._tick_task: asyncio.Task[None] | None = None
        self.host = "127.0.0.1"
        self.port = 4840
        self._tick = 0
        self._nodes: dict[str, Any] = {}
        self._value_types: dict[str, ua.VariantType] = {}

    @property
    def running(self) -> bool:
        return (
            self._server is not None
            and self._serve_task is not None
            and not self._serve_task.done()
        )

    @property
    def endpoint(self) -> str:
        return f"opc.tcp://{self.host}:{self.port}/emulator/"

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(self._nodes)

    def bind(self, generator: TagGenerator) -> None:
        """Bind the shared profile-driven snapshot provider."""
        if self.running:
            raise RuntimeError("cannot bind while server is running")
        self._generator = generator

    async def start(self, host: str = "127.0.0.1", port: int = 4840) -> None:
        """Start the read-only OPC UA server and snapshot ticker."""
        if self.running:
            return
        if self._generator is None:
            raise RuntimeError("TagGenerator is not bound")
        self.host = host
        self.port = _free_port(host) if port == 0 else port

        server = Server()
        await server.init()
        server.set_endpoint(self.endpoint)
        namespace = await server.register_namespace("urn:shipsense:emulator")
        objects = server.get_objects_node()
        emulator = await objects.add_object(namespace, "Emulator")
        snapshot = self._generator.tick(0)
        self._nodes = {}
        self._value_types = {}
        for signal in self._generator.profile["signals"]:
            value_type = _variant_type(signal.get("value_type", "float32"))
            native_id = signal.get("native_ids", {}).get("opcua")
            if native_id is None:
                continue
            native_id = str(native_id)
            node = await emulator.add_variable(
                ua.NodeId.from_string(native_id),
                str(signal["signal_id"]),
                _coerce_value(snapshot.get(native_id), value_type),
                value_type,
            )
            await node.set_read_only()
            self._nodes[native_id] = node
            self._value_types[native_id] = value_type

        await server.start()
        self._server = server
        self._serve_task = asyncio.create_task(
            asyncio.Event().wait(),
            name="emulator-opcua-server-lifecycle",
        )
        self._tick_task = asyncio.create_task(
            self._tick_loop(),
            name="emulator-opcua-ticker",
        )

    async def stop(self) -> None:
        """Stop the server and ticker; safe to call repeatedly."""
        if self._tick_task is not None:
            self._tick_task.cancel()
            await asyncio.gather(self._tick_task, return_exceptions=True)
            self._tick_task = None
        if self._server is not None:
            await self._server.stop()
        if self._serve_task is not None:
            self._serve_task.cancel()
            await asyncio.gather(self._serve_task, return_exceptions=True)
            self._serve_task = None
        self._server = None
        self._nodes.clear()

    async def _tick_loop(self) -> None:
        while True:
            tick_hz = float(self._generator.profile.get("tick_hz", 1.0))
            await asyncio.sleep(1.0 / tick_hz)
            await self._update_snapshot(self._generator.tick(self._tick + 1))
            self._tick += 1

    async def _update_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        writes = [
            node.write_value(
                _coerce_value(
                    snapshot[native_id], self._value_types[native_id]
                ),
                self._value_types[native_id],
            )
            for native_id, node in self._nodes.items()
            if native_id in snapshot
        ]
        if writes:
            await asyncio.gather(*writes)


def _free_port(host: str) -> int:
    with socket.socket() as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _coerce_value(value: Any, value_type: str | ua.VariantType) -> Any:
    variant_type = (
        value_type
        if isinstance(value_type, ua.VariantType)
        else _variant_type(value_type)
    )
    if variant_type in (ua.VariantType.Float, ua.VariantType.Double):
        return float(value)
    if variant_type in (
        ua.VariantType.Int16,
        ua.VariantType.UInt16,
        ua.VariantType.Int32,
        ua.VariantType.UInt32,
        ua.VariantType.Int64,
        ua.VariantType.UInt64,
    ):
        return int(value)
    if variant_type == ua.VariantType.Boolean:
        return bool(value)
    if variant_type == ua.VariantType.String:
        return str(value)
    return value


def _variant_type(value_type: str) -> ua.VariantType:
    return {
        "boolean": ua.VariantType.Boolean,
        "float32": ua.VariantType.Float,
        "float64": ua.VariantType.Double,
        "int16": ua.VariantType.Int16,
        "uint16": ua.VariantType.UInt16,
        "int32": ua.VariantType.Int32,
        "uint32": ua.VariantType.UInt32,
        "string": ua.VariantType.String,
    }.get(value_type, ua.VariantType.Variant)
