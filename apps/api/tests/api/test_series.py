from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.dependencies import get_db, get_semantic_engine
from app.main import app
from app.semantic.engine import SemanticEngine
from app.telemetry.service import SampleLike


FIXTURE = Path(__file__).parents[2] / "fixtures" / "ship-pack-min"


class Row:
    def __init__(self, timestamp: datetime, value: float | None, quality: int) -> None:
        self.official_ts = timestamp
        self.value = value
        self.quality = quality


@pytest.fixture
def loaded_engine() -> SemanticEngine:
    engine = SemanticEngine()
    engine.load(FIXTURE)
    return engine


@pytest.mark.asyncio
async def test_series_endpoint_returns_downsampled_points(
    client, loaded_engine: SemanticEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    start = datetime(2026, 7, 19, tzinfo=timezone.utc)
    rows: list[SampleLike] = [
        Row(start + timedelta(seconds=1), 10.0, 0),
        Row(start + timedelta(seconds=2), 20.0, 4),
    ]

    async def fake_fetch_samples(*_args: object, **_kwargs: object) -> list[SampleLike]:
        return rows

    monkeypatch.setattr("app.telemetry.service.fetch_samples", fake_fetch_samples)
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_semantic_engine] = lambda: loaded_engine
    try:
        response = await client.get(
            "/api/series",
            params={
                "tag": "TAG_GOOD",
                "from": start.isoformat(),
                "to": (start + timedelta(minutes=1)).isoformat(),
                "resolution": "1m",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["tag_id"] == "TAG_GOOD"
    assert body["resolution"] == "1m"
    assert body["points"][0]["quality"] == "quarantine"
    assert body["points"][0]["value"] == 15.0


@pytest.mark.asyncio
async def test_series_endpoint_rejects_unknown_tag(client, loaded_engine: SemanticEngine) -> None:
    app.dependency_overrides[get_db] = lambda: object()
    app.dependency_overrides[get_semantic_engine] = lambda: loaded_engine
    try:
        response = await client.get(
            "/api/series",
            params={
                "tag": "UNKNOWN",
                "from": "2026-07-19T00:00:00Z",
                "to": "2026-07-19T01:00:00Z",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TAG_NOT_FOUND"


@pytest.mark.asyncio
async def test_series_endpoint_rejects_window_over_limit(client) -> None:
    response = await client.get(
        "/api/series",
        params={
            "tag": "TAG_GOOD",
            "from": "2026-01-01T00:00:00Z",
            "to": "2026-04-02T00:00:00Z",
        },
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "WINDOW_TOO_LARGE"
