from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.settings import settings
from app.mnemo.service import MnemoService
from app.telemetry.service import get_latest_value_cache
from app.stream.models import parse_message
from app.stream.protocol import ack_frame, cursor_expired_frame, hello_frame
from app.stream.ring_buffer import CursorExpired

router = APIRouter(tags=["stream"])


@router.websocket("/stream")
async def stream(websocket: WebSocket) -> None:
    bridge = websocket.app.state.stream_bridge
    await bridge.connections.connect(websocket)
    try:
        await websocket.send_json(hello_frame(settings.API_WS_BUFFER_SIZE))
        while True:
            try:
                message = parse_message(await websocket.receive_json())
            except ValueError as exc:
                await websocket.send_json(
                    {"type": "error", "code": "INVALID_MESSAGE", "message": str(exc)}
                )
                continue

            if message.action == "ping":
                await websocket.send_json({"type": "pong", "server_ts": hello_frame(0)["server_ts"]})
                continue
            if message.action == "unsubscribe":
                await bridge.connections.subscribe(websocket, set())
                continue

            channels = list(dict.fromkeys(message.channels))
            mnemo_channels = [channel for channel in channels if channel.startswith("mnemo:")]
            if mnemo_channels:
                service = MnemoService(settings.SHIP_PACK_PATH, get_latest_value_cache())
                try:
                    bound_tags = set().union(
                        *(
                            service.bound_tags(channel.removeprefix("mnemo:"))
                            for channel in mnemo_channels
                        )
                    )
                except LookupError:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "code": "MNEMO_SCHEMA_NOT_FOUND",
                            "message": "Unknown mnemo schema",
                        }
                    )
                    continue
                message_tags = set(message.tags or [])
                filtered_tags = bound_tags if not message_tags else message_tags & bound_tags
                await bridge.connections.subscribe(websocket, set(mnemo_channels), filtered_tags)
                await websocket.send_json(ack_frame(message.subscription_id, mnemo_channels, {}, {}))
                continue
            if "values" in channels and not message.tags:
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "TAGS_REQUIRED",
                        "message": "tags are required for values subscriptions",
                    }
                )
                continue
            if message.tags and len(message.tags) > settings.API_WS_MAX_TAGS:
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "TOO_MANY_TAGS",
                        "message": "subscription exceeds API_WS_MAX_TAGS",
                    }
                )
                continue

            replay: dict[str, int] = {}
            oldest_available: dict[str, int] = {}
            expired = False
            for channel in channels:
                cursor = message.resume_cursor.get(channel, 0)
                try:
                    frames = bridge.ring.replay(channel, cursor)
                except CursorExpired as exc:
                    await websocket.send_json(cursor_expired_frame(channel, exc.oldest_available))
                    expired = True
                    break
                for frame in frames:
                    await websocket.send_json(frame)
                replay[channel] = len(frames)
                oldest_available[channel] = bridge.ring.oldest_available(channel)
            if expired:
                continue
            await bridge.connections.subscribe(websocket, set(channels), set(message.tags or []))
            await websocket.send_json(
                ack_frame(message.subscription_id, channels, replay, oldest_available)
            )
    except WebSocketDisconnect:
        pass
    finally:
        await bridge.connections.disconnect(websocket)
