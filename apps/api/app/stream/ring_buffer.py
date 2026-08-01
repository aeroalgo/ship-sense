from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any


@dataclass
class CursorExpired(Exception):
    oldest_available: int


class RingBuffer:
    def __init__(self, size: int) -> None:
        if size < 1:
            raise ValueError("ring buffer size must be positive")
        self._size = size
        self._next_cursor = defaultdict(lambda: 1)
        self._frames: dict[str, deque[dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=self._size)
        )

    def append(self, channel: str, frame: dict[str, Any]) -> dict[str, Any]:
        frame = {**frame, "cursor": self._next_cursor[channel]}
        self._next_cursor[channel] += 1
        self._frames[channel].append(frame)
        return frame

    def replay(self, channel: str, after_cursor: int) -> list[dict[str, Any]]:
        frames = self._frames[channel]
        oldest = self.oldest_available(channel)
        if frames and after_cursor < oldest - 1:
            raise CursorExpired(oldest)
        return [frame for frame in frames if frame["cursor"] > after_cursor]

    def oldest_available(self, channel: str) -> int:
        frames = self._frames[channel]
        return frames[0]["cursor"] if frames else self._next_cursor[channel]
