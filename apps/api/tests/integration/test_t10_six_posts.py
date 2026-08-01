"""s20 T10 WebSocket capacity and reconnect contract."""

from contextlib import ExitStack

from fastapi.testclient import TestClient

from app.main import app
from app.stream.ring_buffer import RingBuffer


def test_six_stream_connections_receive_independent_posts() -> None:
    with TestClient(app) as client:
        app.state.stream_bridge.ring = RingBuffer(size=16)
        with ExitStack() as stack:
            sockets = [stack.enter_context(client.websocket_connect("/api/stream")) for _ in range(6)]
            for websocket in sockets:
                assert websocket.receive_json()["type"] == "hello"
                websocket.send_json(
                    {
                        "action": "subscribe",
                        "subscription_id": "t10",
                        "channels": ["events"],
                    }
                )
            for websocket in sockets:
                assert websocket.receive_json()["type"] == "ack"

            app.state.stream_bridge.publish(
                "events",
                {"channel": "events", "event": {"id": "t10-event"}},
            )

            for websocket in sockets:
                frame = websocket.receive_json()
                assert frame["type"] == "event"
                assert frame["cursor"] == 1
                assert frame["event"]["id"] == "t10-event"


def test_reconnect_replays_from_client_cursor_after_disconnect() -> None:
    with TestClient(app) as client:
        app.state.stream_bridge.ring = RingBuffer(size=8)
        with client.websocket_connect("/api/stream") as websocket:
            websocket.receive_json()
            websocket.send_json(
                {
                    "action": "subscribe",
                    "subscription_id": "first",
                    "channels": ["events"],
                }
            )
            assert websocket.receive_json()["type"] == "ack"

        app.state.stream_bridge.publish(
            "events",
            {"channel": "events", "event": {"id": "after-disconnect"}},
        )

        with client.websocket_connect("/api/stream") as websocket:
            assert websocket.receive_json()["type"] == "hello"
            websocket.send_json(
                {
                    "action": "subscribe",
                    "subscription_id": "reconnect",
                    "channels": ["events"],
                    "resume_cursor": {"events": 0},
                }
            )
            assert websocket.receive_json()["event"]["id"] == "after-disconnect"
            ack = websocket.receive_json()
            assert ack["type"] == "ack"
            assert ack["replay"] == {"events": 1}
