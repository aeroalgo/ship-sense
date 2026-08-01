from pathlib import Path

import pytest

from app.core.dependencies import get_session_service
from app.core.settings import settings
from app.main import app
from app.session.service import SessionService


class _Result:
    rowcount = 1


class _Db:
    async def execute(self, _statement):
        return _Result()

    async def commit(self):
        return None


@pytest.fixture(autouse=True)
def session_service(monkeypatch: pytest.MonkeyPatch) -> None:
    pack = Path(__file__).parents[2] / "fixtures" / "ship-pack-min"
    monkeypatch.setattr(settings, "SHIP_PACK_PATH", str(pack))
    service = SessionService(pack)
    app.dependency_overrides[get_session_service] = lambda: service
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_roster_returns_active_tiles_sorted(client) -> None:
    response = await client.get("/api/watch/roster")

    assert response.status_code == 200
    assert [item["person_id"] for item in response.json()["items"]] == ["ivanov", "petrov"]


@pytest.mark.asyncio
async def test_session_lifecycle_sets_cookie_and_writes_events(client, monkeypatch: pytest.MonkeyPatch) -> None:
    written = []

    async def capture(self, events):
        written.extend(events)
        return len(events)

    monkeypatch.setattr("app.api.v1.endpoints.session.EventsRepo.insert_batch", capture)
    response = await client.post("/api/session", json={"person_id": "ivanov"},)

    assert response.status_code == 201
    assert response.cookies.get("shipsense_session")
    assert written[0].event_name == "session_started"

    ended = await client.delete("/api/session")
    assert ended.status_code == 204
    assert written[-1].event_name == "session_ended"
    assert written[-1].params["reason"] == "logout"


@pytest.mark.asyncio
async def test_session_rejects_inactive_or_unknown_person(client) -> None:
    response = await client.post("/api/session", json={"person_id": "inactive"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PERSON_NOT_IN_ROSTER"
