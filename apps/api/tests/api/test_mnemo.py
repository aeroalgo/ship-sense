from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.telemetry.service import LatestValueCache


PACK_ROOT = Path(__file__).parents[4] / "ship-pack" / "makarov"


@pytest.fixture
def mnemo_cache() -> LatestValueCache:
    cache = LatestValueCache()
    cache.set("TAI4101", 412, quality="good")
    cache.set("TAI4102", 400, quality="quarantine")
    return cache


def test_mnemo_list_and_detail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SHIP_PACK_PATH", str(PACK_ROOT))

    with TestClient(app) as client:
        response = client.get("/api/mnemo/schemas")
        assert response.status_code == 200
        assert response.json()["items"] == [
            {
                "schema_id": "engine_diesel_main",
                "screen": 2,
                "svg_path": "/static/mnemo/engine_diesel_main.svg",
                "revision": 3,
                "bindings_count": 4,
            }
        ]

        response = client.get("/api/mnemo/schemas/engine_diesel_main")
        assert response.status_code == 200
        assert response.json()["revision"] == 3
        assert response.json()["elements"][0]["element_id"] == "cyl_01_temp"


@pytest.mark.asyncio
async def test_mnemo_values_project_quarantine_to_unknown(
    client, monkeypatch: pytest.MonkeyPatch, mnemo_cache: LatestValueCache
) -> None:
    from app.api.v1.endpoints.mnemo import get_mnemo_cache

    monkeypatch.setattr(settings, "SHIP_PACK_PATH", str(PACK_ROOT))
    app.dependency_overrides[get_mnemo_cache] = lambda: mnemo_cache
    try:
        response = await client.get("/api/mnemo/schemas/engine_diesel_main/values")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    items = {item["element_id"]: item for item in response.json()["items"]}
    assert items["cyl_01_temp"]["value"] == 412
    assert items["cyl_01_temp"]["status"] == "ok"
    assert items["cyl_02_temp"]["value"] is None
    assert items["cyl_02_temp"]["status"] == "unknown"
    assert items["exhaust_deviation"]["value"] is None
    assert items["exhaust_deviation"]["status"] == "unknown"


def test_mnemo_unknown_schema_and_generator_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SHIP_PACK_PATH", str(PACK_ROOT))

    with TestClient(app) as client:
        response = client.get("/api/mnemo/schemas/not-found")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "MNEMO_SCHEMA_NOT_FOUND"

        response = client.get("/api/mnemo/schemas?include_generators=true")
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "MNEMO_GENERATORS_DISABLED"


def test_mnemo_ws_filters_unbound_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.stream.ring_buffer import RingBuffer

    monkeypatch.setattr(settings, "SHIP_PACK_PATH", str(PACK_ROOT))
    with TestClient(app) as client:
        app.state.stream_bridge.ring = RingBuffer(size=10)
        with client.websocket_connect("/api/stream") as websocket:
            assert websocket.receive_json()["type"] == "hello"
            websocket.send_json(
                {
                    "action": "subscribe",
                    "subscription_id": "mnemo-1",
                    "channels": ["mnemo:engine_diesel_main"],
                }
            )
            assert websocket.receive_json()["type"] == "ack"
            app.state.stream_bridge.publish(
                "mnemo:engine_diesel_main",
                {
                    "channel": "mnemo:engine_diesel_main",
                    "schema_id": "engine_diesel_main",
                    "tag_id": "TAI9999",
                    "value": 1,
                },
            )
            app.state.stream_bridge.publish(
                "mnemo:engine_diesel_main",
                {
                    "channel": "mnemo:engine_diesel_main",
                    "schema_id": "engine_diesel_main",
                    "tag_id": "TAI4101",
                    "value": 412,
                },
            )
            frame = websocket.receive_json()
            assert frame["tag_id"] == "TAI4101"
            assert frame["schema_id"] == "engine_diesel_main"
