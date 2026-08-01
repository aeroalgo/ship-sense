from datetime import datetime, timezone
from typing import Any


def hello_frame(buffer_size: int) -> dict[str, Any]:
    return {
        "type": "hello",
        "protocol": 1,
        "server_ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "buffers": {"events": buffer_size, "values": buffer_size},
    }


def ack_frame(
    subscription_id: str | None,
    channels: list[str],
    replay: dict[str, int],
    oldest_available: dict[str, int],
) -> dict[str, Any]:
    return {
        "type": "ack",
        "subscription_id": subscription_id,
        "channels": channels,
        "replay": replay,
        "oldest_available": oldest_available,
    }


def cursor_expired_frame(channel: str, oldest_available: int) -> dict[str, Any]:
    return {
        "type": "error",
        "code": "CURSOR_EXPIRED",
        "message": "Resume cursor older than ring buffer",
        "channel": channel,
        "oldest_available": oldest_available,
        "hint": "Refetch GET /api/events?from=...",
    }
