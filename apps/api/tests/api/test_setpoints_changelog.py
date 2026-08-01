from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.setpoints.service import SetpointsService


def test_changelog_filters_malformed_events_and_sorts() -> None:
    rows = [
        SimpleNamespace(
            event_id="b",
            official_ts=datetime(2026, 1, 2, tzinfo=timezone.utc),
            source="ops",
            params={"tag_id": "SKT002", "old_value": 3, "new_value": 4, "unit": "bar"},
        ),
        SimpleNamespace(
            event_id="a",
            official_ts=datetime(2026, 1, 1, tzinfo=timezone.utc),
            source="ops",
            params={"tag_id": "SKT002", "old_value": 2, "new_value": 3, "unit": "bar", "actor": "watch"},
        ),
        SimpleNamespace(
            event_id="bad",
            official_ts=datetime(2026, 1, 3, tzinfo=timezone.utc),
            source="ops",
            params={"tag_id": "SKT002"},
        ),
    ]

    result = SetpointsService.changelog_rows(rows)

    assert [item.id for item in result.items] == ["a", "b"]
    assert result.items[0].actor == "watch"


@pytest.mark.asyncio
async def test_changelog_endpoint_rejects_reversed_utc_range(client) -> None:
    response = await client.get(
        "/api/setpoints/changelog",
        params={"from": "2026-01-02T00:00:00Z", "to": "2026-01-01T00:00:00Z"},
    )

    assert response.status_code == 422
