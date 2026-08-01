from datetime import datetime, timezone

import pytest

from app.core.dependencies import get_db
from app.main import app
from app.warnings.schemas import DriftWarning, WarningStatus, WarningTransition
from app.warnings.service import WarningService


UTC = timezone.utc


def warning(tag_id: str, status: WarningStatus = WarningStatus.ACTIVE) -> DriftWarning:
    return DriftWarning(
        tag_id=tag_id,
        asset_id="engine-1",
        status=status,
        raw_value=92.0,
        ewma_value=91.0,
        setpoint=100.0,
        setpoint_source="ship-pack",
        unit="bar",
        threshold_pct=0.9,
        comparison="high",
        since=datetime(2026, 7, 26, 8, tzinfo=UTC),
        config_version="b13-v1",
    )


@pytest.mark.asyncio
async def test_warnings_endpoint_filters_active_and_tag(client, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {}

    async def list_active(self, session, *, active, tag_id, asset_id, since):
        calls.update(active=active, tag_id=tag_id, asset_id=asset_id, since=since)
        return [warning(tag_id)]

    monkeypatch.setattr(WarningService, "list_active", list_active)
    app.dependency_overrides[get_db] = lambda: object()
    try:
        response = await client.get(
            "/api/warnings",
            params={"active": "true", "tag_id": "TAI4101", "asset_id": "engine-1"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["tag_id"] == "TAI4101"
    assert calls == {"active": True, "tag_id": "TAI4101", "asset_id": "engine-1", "since": None}


@pytest.mark.asyncio
async def test_warnings_history_supports_offset_pagination(client, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {}
    transition = WarningTransition(
        tag_id="TAI4101",
        from_status=WarningStatus.CLEARED,
        to_status=WarningStatus.ACTIVE,
        occurred_at=datetime(2026, 7, 26, 8, tzinfo=UTC),
        warning=warning("TAI4101"),
    )

    async def history(self, session, *, tag_id, asset_id, since, limit, offset):
        calls.update(tag_id=tag_id, asset_id=asset_id, since=since, limit=limit, offset=offset)
        return [transition], True

    monkeypatch.setattr(WarningService, "history", history)
    app.dependency_overrides[get_db] = lambda: object()
    try:
        response = await client.get(
            "/api/warnings/history",
            params={"tag_id": "TAI4101", "limit": 1, "offset": 2},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["to_status"] == "active"
    assert response.json()["has_more"] is True
    assert calls == {"tag_id": "TAI4101", "asset_id": None, "since": None, "limit": 1, "offset": 2}


def test_warnings_openapi_has_no_ai_text() -> None:
    spec = app.openapi()
    assert "/api/warnings" in spec["paths"]
    assert "/api/warnings/history" in spec["paths"]
    assert all(
        "ai" not in str(value).lower()
        for value in spec["paths"].values()
    )
