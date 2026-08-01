"""s20 integration seam: deterministic emulator-shaped reports and warnings."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.core.dependencies import get_db
from app.main import app
from app.reports.service import ReportsService
from app.warnings.schemas import DriftWarning, WarningStatus
from app.warnings.service import WarningService


UTC = timezone.utc
FROM = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
TO = datetime(2026, 8, 1, 1, 0, tzinfo=UTC)


def _warning(tag_id: str) -> DriftWarning:
    return DriftWarning(
        tag_id=tag_id,
        asset_id="engine-1",
        status=WarningStatus.ACTIVE,
        raw_value=95.0,
        ewma_value=93.0,
        setpoint=100.0,
        setpoint_source="ship-pack",
        unit="bar",
        threshold_pct=0.9,
        comparison="high",
        since=FROM,
        config_version="b13-v1",
    )


@pytest.mark.asyncio
async def test_emulator_report_and_warning_paths_keep_quality_contract(
    client, monkeypatch: pytest.MonkeyPatch
) -> None:
    events = [
        SimpleNamespace(
            event_id="event-1",
            official_ts=FROM,
            event_name="alarm.HH",
            source="emulator",
            params={"asset_id": "engine-1", "tag_id": "TAI4101"},
            severity=2,
        )
    ]
    samples = [
        SimpleNamespace(
            tag_id="TAI4101",
            official_ts=FROM,
            value=95.0,
            quality=0,
        ),
        SimpleNamespace(
            tag_id="DIRT0001",
            official_ts=FROM,
            value=1.0,
            quality=4,
        ),
    ]

    async def load_events(self, _session, _from_ts, _to_ts):
        return events

    async def load_samples(self, _session, _from_ts, _to_ts):
        return samples

    async def load_quarantine(self, _session, _from_ts, _to_ts):
        return []

    async def list_active(self, _session, *, active, tag_id, asset_id, since):
        return [_warning(tag_id or "TAI4101")]

    monkeypatch.setattr(ReportsService, "_load_events", load_events)
    monkeypatch.setattr(ReportsService, "_load_samples", load_samples)
    monkeypatch.setattr(ReportsService, "_load_quarantine", load_quarantine)
    monkeypatch.setattr(WarningService, "list_active", list_active)
    app.dependency_overrides[get_db] = lambda: object()
    try:
        report = await client.get(
            "/api/reports/watch",
            params={"from": FROM.isoformat(), "to": TO.isoformat()},
        )
        warnings = await client.get("/api/warnings", params={"active": "true"})
    finally:
        app.dependency_overrides.clear()

    assert report.status_code == 200
    assert report.json()["summary"]["events_count"] == 1
    assert "DIRT0001" in report.json()["data_quality"]["quarantine_tags"]
    assert warnings.status_code == 200
    assert warnings.json()["items"][0]["tag_id"] == "TAI4101"
    assert "artificial intelligence" not in report.text.lower()
    assert "artificial intelligence" not in warnings.text.lower()
