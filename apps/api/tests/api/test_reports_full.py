from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.core.dependencies import get_db, get_session_service
from app.main import app
from app.reports.jobs import ReportJobStore
from app.reports.schemas import ReportGenerateRequest
from app.session.service import SessionService


UTC = timezone.utc


def request() -> ReportGenerateRequest:
    return ReportGenerateRequest(
        type="watch",
        period={
            "from": datetime(2026, 7, 31, 22, 0, tzinfo=UTC),
            "to": datetime(2026, 8, 1, 6, 0, tzinfo=UTC),
            "boundary_rule": "watch_explicit",
        },
    )


@pytest.mark.asyncio
async def test_report_job_runs_to_done() -> None:
    store = ReportJobStore()
    expected = uuid4()

    async def generate(_request):
        return {"report_id": str(expected)}

    job = store.create(request(), generate)
    for _ in range(20):
        current = store.get(job.job_id)
        if current and current.status == "done":
            break
        import asyncio

        await asyncio.sleep(0)

    current = store.get(job.job_id)
    assert current is not None
    assert current.status == "done"
    assert current.report == {"report_id": str(expected)}


@pytest.mark.asyncio
async def test_catalog_is_separate_from_report_runs(client) -> None:
    response = await client.get("/api/reports/catalog")
    assert response.status_code == 200
    assert {item["type"] for item in response.json()["items"]} == {
        "watch",
        "daily_noon",
        "fuel",
        "register",
    }


@pytest.mark.asyncio
async def test_watch_schedule_uses_active_roster(client) -> None:
    service = SessionService("apps/api/fixtures/ship-pack-min")
    app.dependency_overrides[get_session_service] = lambda: service
    try:
        response = await client.get("/api/watch/schedule")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert [item["person_id"] for item in response.json()["items"]] == ["ivanov", "petrov"]
    assert response.json()["boundary_rule"] == "watch_explicit"
