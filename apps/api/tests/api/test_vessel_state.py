from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.settings import settings
from app.main import app
from app.telemetry.service import get_latest_value_cache
from app.vessel.service import VesselStateService
from app.vessel.schemas import VesselMode
from app.vessel.store import InMemoryOverrideStore
from app.api.v1.endpoints.vessel import get_vessel_service


FIXTURE = Path(__file__).parents[2] / "fixtures" / "ship-pack-min"
NOW = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def vessel_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SHIP_PACK_PATH", str(FIXTURE))
    get_latest_value_cache().set("SKT001", None)
    app.dependency_overrides.clear()


def _service() -> VesselStateService:
    return VesselStateService(str(FIXTURE), get_latest_value_cache(), InMemoryOverrideStore())


@pytest.mark.asyncio
async def test_vessel_state_uses_rpm_threshold(client) -> None:
    get_latest_value_cache().set("SKT001", 400, timestamp=datetime.now(timezone.utc))
    app.dependency_overrides[get_vessel_service] = _service

    response = await client.get("/api/vessel/state")

    assert response.status_code == 200
    assert response.json()["mode"] == "transit"
    assert response.json()["rpm_ge1"] == 400.0


@pytest.mark.asyncio
async def test_vessel_state_fails_closed_for_stale_rpm(client) -> None:
    get_latest_value_cache().set(
        "SKT001", 500, quality="stale", timestamp=NOW - timedelta(seconds=1)
    )
    app.dependency_overrides[get_vessel_service] = _service

    response = await client.get("/api/vessel/state")

    assert response.status_code == 200
    assert response.json()["mode"] == "anchorage"
    assert response.json()["rpm_ge1"] is None


@pytest.mark.asyncio
async def test_vessel_override_expires_without_background_reset(client) -> None:
    service = _service()
    await service.override(VesselMode.TRANSIT, 1, now=NOW)
    state = await service.state(now=NOW + timedelta(minutes=1))

    assert state.mode == VesselMode.ANCHORAGE
    assert state.override_mode is None


@pytest.mark.asyncio
async def test_vessel_openapi_has_only_override_mutation(client) -> None:
    response = await client.get("/api/openapi.json")
    paths = response.json()["paths"]

    assert set(paths["/api/vessel/state"]) == {"get"}
    assert set(paths["/api/vessel/state/override"]) == {"post"}
