from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.api.v1.endpoints.admin_audit import get_access_audit
from app.api.v1.endpoints.admin_storage import get_storage
from app.audit.models import AccessAudit
from app.audit.writer import AccessAuditWriter
from app.core.dependencies import get_db, get_session_service
from app.core.settings import settings
from app.main import app
from app.session.service import SessionService


class _Db:
    async def execute(self, _statement):
        result = MagicMock()
        result.mappings.return_value.first.return_value = None
        return result


@pytest.fixture
def admin_api(monkeypatch: pytest.MonkeyPatch):
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
    service = SessionService(pack)

    async def ignore_events(self, events):
        return len(events)

    async def ignore_audit(self, record):
        return None

    monkeypatch.setattr("app.api.v1.endpoints.session.EventsRepo.insert_batch", ignore_events)
    monkeypatch.setattr("app.api.v1.endpoints.session.AccessAuditWriter.append", ignore_audit)
    app.dependency_overrides[get_session_service] = lambda: service
    app.dependency_overrides[get_db] = lambda: _Db()
    yield
    app.dependency_overrides.clear()
    (pack / "roster.yaml").write_text(roster, encoding="utf-8")


@pytest.mark.asyncio
async def test_storage_requires_admin_role(client, admin_api) -> None:
    await client.post("/api/session", json={"person_id": "ivanov"})

    response = await client.get("/api/admin/storage")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_storage_reports_degraded_without_snapshot_or_backup(client, admin_api, monkeypatch) -> None:
    await client.post("/api/session", json={"person_id": "petrov"})
    monkeypatch.setattr("app.api.v1.endpoints.admin_storage._raid_status", lambda: {"degraded": False})
    monkeypatch.setattr("app.api.v1.endpoints.admin_storage._latest_backup", lambda: False)

    response = await client.get("/api/admin/storage")

    assert response.status_code == 200
    assert response.json()["backup_last_ok"] is False
    assert response.json()["degraded"] is True


@pytest.mark.asyncio
async def test_access_audit_passes_pagination_to_writer(client, admin_api, monkeypatch) -> None:
    await client.post("/api/session", json={"person_id": "petrov"})
    calls = {}
    record = AccessAudit(ts="2026-08-01T00:00:00Z", person_id="petrov", action="login")

    async def list_rows(self, *, limit, offset):
        calls.update(limit=limit, offset=offset)
        return [record]

    monkeypatch.setattr(AccessAuditWriter, "list", list_rows)

    response = await client.get("/api/admin/access/audit?limit=2&offset=4")

    assert response.status_code == 200
    assert calls == {"limit": 2, "offset": 4}
    assert response.json()["items"][0]["action"] == "login"
    assert response.json()["limit"] == 2
    assert response.json()["offset"] == 4
