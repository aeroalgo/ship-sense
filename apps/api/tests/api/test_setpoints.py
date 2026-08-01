from pathlib import Path

import pytest

from app.core.settings import settings


FIXTURE = Path(__file__).parents[2] / "fixtures" / "ship-pack-min"


@pytest.fixture(autouse=True)
def ship_pack_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SHIP_PACK_PATH", str(FIXTURE))


@pytest.mark.asyncio
async def test_setpoints_endpoint_returns_active_items(client) -> None:
    response = await client.get("/api/setpoints")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "tag_id": "sp_TAI4101_HH",
                "value": 80.0,
                "unit": "°C",
                "label": "HH TAI4101",
                "effective_from": "2026-01-15T00:00:00Z",
            }
        ]
    }


@pytest.mark.asyncio
async def test_setpoint_history_endpoint_returns_segments(client) -> None:
    response = await client.get(
        "/api/setpoints/history", params={"tag": "sp_TAI4101_HH"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "tag_id": "sp_TAI4101_HH",
        "segments": [
            {
                "from_ts": "2026-01-01T00:00:00Z",
                "to_ts": "2026-01-15T00:00:00Z",
                "value": 78.0,
            },
            {
                "from_ts": "2026-01-15T00:00:00Z",
                "to_ts": None,
                "value": 80.0,
            },
        ],
    }


@pytest.mark.asyncio
async def test_setpoint_history_rejects_unknown_tag(client) -> None:
    response = await client.get(
        "/api/setpoints/history", params={"tag": "unknown"}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TAG_NOT_FOUND"


@pytest.mark.asyncio
async def test_setpoints_are_read_only_in_openapi(client) -> None:
    response = await client.get("/api/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert set(paths["/api/setpoints"]) == {"get"}
    assert set(paths["/api/setpoints/history"]) == {"get"}
