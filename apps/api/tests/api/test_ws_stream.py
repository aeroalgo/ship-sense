from fastapi.testclient import TestClient

from app.main import app
from app.stream.ring_buffer import CursorExpired, RingBuffer


def test_ring_buffer_replays_after_cursor_and_reports_expiry() -> None:
    ring = RingBuffer(size=2)
    ring.append("events", {"channel": "events", "event": {"id": "e1"}})
    ring.append("events", {"channel": "events", "event": {"id": "e2"}})
    ring.append("events", {"channel": "events", "event": {"id": "e3"}})

    assert [frame["cursor"] for frame in ring.replay("events", 1)] == [2, 3]
    assert ring.oldest_available("events") == 2
    try:
        ring.replay("events", 0)
    except CursorExpired as exc:
        assert exc.oldest_available == 2
    else:
        raise AssertionError("expected expired cursor")


def test_ws_subscribe_ack_and_resume() -> None:
    with TestClient(app) as client:
        bridge = app.state.stream_bridge
        bridge.publish("events", {"channel": "events", "event": {"id": "e1"}})
        bridge.publish("events", {"channel": "events", "event": {"id": "e2"}})

        with client.websocket_connect("/api/stream") as websocket:
            assert websocket.receive_json()["type"] == "hello"
            websocket.send_json(
                {
                    "action": "subscribe",
                    "subscription_id": "sub-1",
                    "channels": ["events"],
                    "resume_cursor": {"events": 1},
                }
            )
            assert websocket.receive_json() == {
                "type": "event",
                "cursor": 2,
                "channel": "events",
                "event": {"id": "e2"},
            }
            assert websocket.receive_json() == {
                "type": "ack",
                "subscription_id": "sub-1",
                "channels": ["events"],
                "replay": {"events": 1},
                "oldest_available": {"events": 1},
            }


def test_ws_expired_cursor_returns_error() -> None:
    with TestClient(app) as client:
        bridge = app.state.stream_bridge
        bridge.ring = RingBuffer(size=1)
        for event_id in ("e1", "e2"):
            bridge.publish("events", {"channel": "events", "event": {"id": event_id}})

        with client.websocket_connect("/api/stream") as websocket:
            websocket.receive_json()
            websocket.send_json(
                {
                    "action": "subscribe",
                    "channels": ["events"],
                    "resume_cursor": {"events": 0},
                }
            )
            assert websocket.receive_json() == {
                "type": "error",
                "code": "CURSOR_EXPIRED",
                "message": "Resume cursor older than ring buffer",
                "channel": "events",
                "oldest_available": 2,
                "hint": "Refetch GET /api/events?from=...",
            }
