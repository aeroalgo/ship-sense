import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Subscription:
    channels: set[str]
    tags: set[str] = field(default_factory=set)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[Any, Subscription] = {}
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
        self._loop = asyncio.get_running_loop()
        async with self._lock:
            self._connections[websocket] = Subscription(set())

    def broadcast_threadsafe(self, frame: dict[str, Any]) -> None:
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        loop.call_soon_threadsafe(self._schedule_broadcast, frame)

    def _schedule_broadcast(self, frame: dict[str, Any]) -> None:
        asyncio.create_task(self.broadcast(frame))

    def clear_loop(self) -> None:
        self._loop = None

    async def disconnect(self, websocket: Any) -> None:
        async with self._lock:
            self._connections.pop(websocket, None)

    async def subscribe(
        self, websocket: Any, channels: set[str], tags: set[str] | None = None
    ) -> None:
        async with self._lock:
            self._connections[websocket] = Subscription(channels, tags or set())

    async def broadcast(self, frame: dict[str, Any]) -> None:
        channel = frame.get("channel")
        tag_id = frame.get("tag_id")
        async with self._lock:
            targets = [
                websocket
                for websocket, subscription in self._connections.items()
                if channel in subscription.channels
                and (not subscription.tags or tag_id is None or tag_id in subscription.tags)
            ]


        for websocket in targets:
            try:
                await websocket.send_json(frame)
            except Exception:
                await self.disconnect(websocket)
