from typing import Any

from app.core.settings import settings
from app.stream.connection_manager import ConnectionManager
from app.stream.ring_buffer import RingBuffer


class FanoutBridge:
    def __init__(self) -> None:
        self.ring = RingBuffer(settings.API_WS_BUFFER_SIZE)
        self.connections = ConnectionManager()

    def _append(self, channel: str, frame: dict[str, Any]) -> dict[str, Any]:
        return self.ring.append(channel, {"type": channel[:-1] if channel.endswith("s") else channel, **frame})

    def publish(self, channel: str, frame: dict[str, Any]) -> dict[str, Any]:
        published = self._append(channel, frame)
        self.connections.broadcast_threadsafe(published)
        return published

    async def broadcast(self, channel: str, frame: dict[str, Any]) -> dict[str, Any]:
        published = self._append(channel, frame)
        await self.connections.broadcast(published)
        return published
