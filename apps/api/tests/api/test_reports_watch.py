from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.dependencies import get_db
from app.main import app
from app.reports.service import ReportsService


UTC = timezone.utc
FROM = datetime(2026, 7, 26, 8, 0, tzinfo=UTC)
TO = datetime(2026, 7, 26, 16, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def report_loaders(monkeypatch: pytest.MonkeyPatch) -> None:
    event_id = uuid4()
    events = [
        SimpleNamespace(
            event_id=event_id,
            official_ts=datetime(2026, 7, 26, 10, 0, tzinfo=UTC),
            event_name="alarm.HH",
            source="aps",
            params={"asset_id": "<engine-1>", "kks": "TAI4101"},
            severity=2,
        ),
        SimpleNamespace(
            event_id=uuid4(),
            official_ts=datetime(2026, 7, 26, 10, 0, 30, tzinfo=UTC),
            event_name="protection.trip",
            source="aps",
            params={"asset_id": "engine-1", "kks": "TAI4101", "tag_id": "TAI4101"},
            severity=3,
        ),
    ]
    samples = [
        SimpleNamespace(
            tag_id="unknown_native_40099",
            official_ts=datetime(2026, 7, 26, 10, 1, tzinfo=UTC),
            value=77.0,
            quality=4,
        ),
        SimpleNamespace(
            tag_id="TAI4101",
            official_ts=datetime(2026, 7, 26, 10, 2, tzinfo=UTC),
            value=78.0,
            quality=0,
        ),
    ]

    async def load_events(self, _session, _from_ts, _to_ts):
        return events

    async def load_samples(self, _session, _from_ts, _to_ts):
        return samples

    async def load_quarantine(self, _session, _from_ts, _to_ts):
        return []

    monkeypatch.setattr(ReportsService, "_load_events", load_events)
    monkeypatch.setattr(ReportsService, "_load_samples", load_samples)
    monkeypatch.setattr(ReportsService, "_load_quarantine", load_quarantine)
    app.dependency_overrides[get_db] = lambda: object()
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_reports_catalog_and_watch_json_shape(client) -> None:
    catalog = await client.get("/api/reports")
    assert catalog.status_code == 200
    assert catalog.json() == {
        "items": [
            {
                "type": "watch",
                "title": "Вахтенная сводка",
                "formats": ["json", "html"],
                "description": "Прототип экрана 6; полный B12 — фаза 2",
            }
        ]
    }

    response = await client.get(
        "/api/reports/watch",
        params={"from": FROM.isoformat(), "to": TO.isoformat()},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["period"] == {"from": FROM.isoformat().replace("+00:00", "Z"), "to": TO.isoformat().replace("+00:00", "Z")}
    assert body["watchkeeper"] is None
    assert body["summary"]["events_count"] == 2
    assert body["summary"]["protections_count"] == 1
    assert body["data_quality"]["quarantine_tags"] == ["unknown_native_40099"]
    assert body["data_quality"]["banner"]
    assert len(body["highlights"]) == 2
    assert len(body["tags_snapshot"]) <= 3


@pytest.mark.asyncio
async def test_watch_html_escapes_fields_and_has_quarantine_banner(client) -> None:
    response = await client.get(
        "/api/reports/watch",
        params={"from": FROM.isoformat(), "to": TO.isoformat(), "format": "html"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "&lt;engine-1&gt;" in response.text
    assert "Часть периода под сверкой" in response.text
    assert "application/pdf" not in response.text


@pytest.mark.asyncio
async def test_watch_rejects_invalid_window(client) -> None:
    response = await client.get(
        "/api/reports/watch",
        params={"from": TO.isoformat(), "to": FROM.isoformat()},
    )
    assert response.status_code == 422
