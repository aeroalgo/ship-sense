from datetime import datetime, timezone
import json

import pytest

from app.health.service import HealthService


@pytest.mark.asyncio
async def test_health_service_marks_db_failure_as_degraded(tmp_path) -> None:
    snapshot = tmp_path / "collector.json"
    snapshot.write_text(
        json.dumps(
            {
                "ts": "2026-07-31T10:00:00Z",
                "collector_state": "running",
                "sources": [],
                "queue_raw_depth": 0,
                "queue_canonical_depth": 0,
                "samples_total": 1,
                "events_total": 0,
                "errors_total": 0,
            }
        )
    )

    class BrokenSession:
        async def execute(self, _statement):
            raise OSError("database unavailable")

    result = await HealthService(snapshot_path=snapshot).build_health(BrokenSession())

    assert result.status == "degraded"
    assert result.checks["db"].status == "down"
    assert result.checks["collector"].status == "ok"


def test_sources_status_uses_worst_quality(tmp_path) -> None:
    snapshot = tmp_path / "collector.json"
    snapshot.write_text(
        json.dumps(
            {
                "ts": "2026-07-31T10:00:00Z",
                "collector_state": "running",
                "sources": [
                    {
                        "source_id": "aps",
                        "state": "up",
                        "last_ok_ts": "2026-07-31T10:00:00Z",
                        "tags_active": 4,
                    },
                    {
                        "source_id": "geu",
                        "state": "degraded",
                        "last_ok_ts": "2026-07-31T09:59:00Z",
                        "tags_active": 2,
                        "reconnect_count": 1,
                    },
                ],
            }
        )
    )

    response = HealthService(snapshot_path=snapshot).sources_status()

    assert [item.source_id for item in response.items] == ["aps", "geu"]
    assert response.items[0].quality_summary == "good"
    assert response.items[1].quality_summary == "uncertain"
    assert response.items[1].last_poll_ts == datetime(2026, 7, 31, 9, 59, tzinfo=timezone.utc)
