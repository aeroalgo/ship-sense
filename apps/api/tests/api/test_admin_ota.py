from pathlib import Path

import pytest

from app.api.v1.endpoints.admin_ota import get_ota_coordinator
from app.core.dependencies import get_session_service
from app.core.settings import settings
from app.main import app
from app.session.service import SessionService


@pytest.fixture(autouse=True)
def admin_session(monkeypatch: pytest.MonkeyPatch) -> None:
    pack = Path(__file__).parents[2] / "fixtures" / "ship-pack-min"
    roster = (pack / "roster.yaml").read_text(encoding="utf-8")
    (pack / "roster.yaml").write_text(
        roster.replace(
            'rank: "вахтенный механик"',
            'rank: "вахтенный механик"\n    roles: [watch_officer]',
        ).replace(
            'rank: "старший механик"',
            'rank: "старший механик"\n    roles: [chief_engineer]',
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "SHIP_PACK_PATH", str(pack))
    monkeypatch.setattr("app.api.v1.endpoints.session.EventsRepo.insert_batch", _ignore_events)
    monkeypatch.setattr("app.api.v1.endpoints.session.AccessAuditWriter.append", _ignore_audit)
    monkeypatch.setattr("app.api.v1.endpoints.admin_ota.AccessAuditWriter.append", _ignore_audit)
    service = SessionService(pack)
    app.dependency_overrides[get_session_service] = lambda: service
    coordinator = _TestCoordinator()
    app.dependency_overrides[get_ota_coordinator] = lambda: coordinator
    yield
    app.dependency_overrides.clear()
    (pack / "roster.yaml").write_text(roster, encoding="utf-8")


async def _ignore_events(self, events):
    return len(events)


async def _ignore_audit(self, record):
    return None


class _TestCoordinator:
    def __init__(self) -> None:
        self.approved = False

    async def status(self):
        return {"status": "ready", "update_allowed": True, "approved": self.approved}

    async def approve(self):
        self.approved = True
        return await self.status()

    async def trigger(self):
        if not self.approved:
            raise PermissionError("OTA approval is required")
        return {"status": "triggered", "update_allowed": True, "approved": True}


@pytest.mark.asyncio
async def test_ota_approve_requires_chief_engineer(client) -> None:
    await client.post("/api/session", json={"person_id": "ivanov"})
    response = await client.post("/api/admin/ota/approve")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_chief_engineer_can_approve_and_trigger_ota(client) -> None:
    await client.post("/api/session", json={"person_id": "petrov"})

    approved = await client.post("/api/admin/ota/approve")
    triggered = await client.post("/api/admin/ota/trigger")

    assert approved.status_code == 200
    assert triggered.status_code == 200
    assert triggered.json()["status"] == "triggered"
