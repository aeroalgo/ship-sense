from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from uuid import UUID

from app.events.models import EventSeverity
from app.events.queries_events import fetch_events
from app.events.schemas import EventItem, EventsListResponse


_SEVERITY_BY_CODE = {
    0: EventSeverity.INFO,
    1: EventSeverity.WARNING,
    2: EventSeverity.ALARM,
    3: EventSeverity.PROTECTION,
    4: EventSeverity.PROTECTION,
}


def encode_cursor(timestamp: datetime, event_id: UUID) -> str:
    timestamp = _utc_timestamp(timestamp)
    payload = json.dumps(
        {"id": str(event_id), "ts": timestamp.isoformat().replace("+00:00", "Z")},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_cursor(value: str) -> tuple[datetime, UUID]:
    if "=" in value:
        raise ValueError("cursor must be unpadded base64url")
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("cursor is not valid base64url JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"id", "ts"}:
        raise ValueError("cursor must contain only ts and id")
    try:
        timestamp = datetime.fromisoformat(payload["ts"].replace("Z", "+00:00"))
        event_id = UUID(payload["id"])
    except (TypeError, ValueError) as exc:
        raise ValueError("cursor has invalid ts or id") from exc
    return _utc_timestamp(timestamp), event_id


def _utc_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("cursor timestamp must be UTC")
    return value.astimezone(timezone.utc)


def event_item(row) -> EventItem:
    raw_params = dict(row.params or {})
    asset_id = raw_params.get("asset_id")
    quality = raw_params.get("quality")
    params = {key: value for key, value in raw_params.items() if key not in {"asset_id", "quality"}}
    if row.reconstructed:
        params["reconstructed"] = True
    return EventItem(
        id=str(row.event_id),
        ts=row.official_ts,
        event_name=row.event_name,
        severity=_SEVERITY_BY_CODE.get(row.severity),
        source=row.source,
        asset_id=asset_id,
        params=params,
        quality=quality,
    )


async def list_events(
    session,
    *,
    from_ts: datetime | None,
    to_ts: datetime | None,
    event_names: list[str] | None,
    severities: list[EventSeverity] | None,
    asset_id: str | None,
    source: str | None,
    cursor: tuple[datetime, UUID] | None,
    limit: int,
) -> EventsListResponse:
    rows = await fetch_events(
        session,
        from_ts=from_ts,
        to_ts=to_ts,
        event_names=event_names,
        severities=[_severity_code(value) for value in severities] if severities else None,
        asset_id=asset_id,
        source=source,
        cursor=cursor,
        limit=limit + 1,
    )
    has_more = len(rows) > limit
    page = rows[:limit]
    return EventsListResponse(
        items=[event_item(row) for row in page],
        next_cursor=encode_cursor(page[-1].official_ts, page[-1].event_id) if page else None,
        has_more=has_more,
    )


def _severity_code(value: EventSeverity) -> int:
    return {
        EventSeverity.INFO: 0,
        EventSeverity.WARNING: 1,
        EventSeverity.ALARM: 2,
        EventSeverity.PROTECTION: 3,
    }[value]
