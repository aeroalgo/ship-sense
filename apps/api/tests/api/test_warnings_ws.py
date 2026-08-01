from fastapi.testclient import TestClient

from app.main import app


def test_ws_warnings_channel_pushes_transition() -> None:
    with TestClient(app) as client:
        bridge = app.state.stream_bridge
        with client.websocket_connect("/api/stream") as websocket:
            assert websocket.receive_json()["type"] == "hello"
            websocket.send_json(
                {
                    "action": "subscribe",
                    "subscription_id": "warnings-1",
                    "channels": ["warnings"],
                }
            )
            assert websocket.receive_json()["type"] == "ack"
            bridge.publish(
                "warnings",
                {
                    "channel": "warnings",
                    "warning": {"tag_id": "TAI4101", "to_status": "active"},
                },
            )
            frame = websocket.receive_json()
            assert frame["type"] == "warning"
            assert frame["channel"] == "warnings"
            assert frame["warning"]["tag_id"] == "TAI4101"
            assert "ai" not in str(frame["warning"]["to_status"]).lower()
