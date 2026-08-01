from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.events.service import encode_cursor
from app.core.dependencies import get_db
from app.main import app
from apps.edge.storage.schemas import Event as DBEvent


@pytest.fixture
def event_rows() -> list[DBEvent]:
    now = datetime(2026, 7, 26, 8, 0, tzinfo=timezone.utc)
    return [
        DBEvent(
            event_id=uuid4(),
            idempotency_key="event-1",
            event_name="alarm.HH",
            source="aps",
            source_ts=now,
            edge_ts=now,
            official_ts=now,
            params={"asset_id": "engine-1", "quality": "good"},
            severity=2,
            reconstructed=False,
            ingested_at=now,
        ),
        DBEvent(
            event_id=uuid4(),
            idempotency_key="event-2",
            event_name="session_started",
            source="edge",
            source_ts=now,
            edge_ts=now,
            official_ts=now,
            params={},
            severity=0,
            reconstructed=False,
            ingested_at=now,
        ),
    ]


@pytest.mark.asyncio
async def test_events_endpoint_returns_items_and_reconstruction_header(client, event_rows) -> None:
    class Result:
        def scalars(self):
            return self

        def all(self):
            return event_rows

    class Session:
        async def execute(self, _query):
            return Result()

    app.dependency_overrides[get_db] = lambda: Session()
    try:
        response = await client.get("/api/events", params={"limit": 10})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["items"][0]["asset_id"] == "engine-1"
    assert body["items"][0]["severity"] == "alarm"
    assert body["next_cursor"] is not None
    assert body["has_more"] is False
    assert "X-Events-Reconstruction" not in response.headers


@pytest.mark.asyncio
async def test_events_endpoint_rejects_invalid_cursor(client) -> None:
    response = await client.get("/api/events", params={"cursor": "not-a-cursor"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_CURSOR"


def test_cursor_round_trip() -> None:
    event_id = uuid4()
    timestamp = datetime(2026, 7, 26, 8, 0, tzinfo=timezone.utc)

    decoded = __import__("app.api.v1.endpoints.events", fromlist=["decode_cursor"]).decode_cursor(
        encode_cursor(timestamp, event_id)
    )

    assert decoded == (timestamp, event_id)
