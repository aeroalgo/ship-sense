from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_db
from app.events.models import EventSeverity
from app.events.schemas import EventsListResponse
from app.events.service import decode_cursor, list_events

router = APIRouter(tags=["events"])


@router.get("/events", response_model=EventsListResponse, operation_id="getEvents")
async def get_events(
    response: Response,
    from_ts: Annotated[datetime | None, Query(alias="from")] = None,
    to: datetime | None = None,
    event_name: Annotated[list[str] | None, Query()] = None,
    severity: Annotated[list[EventSeverity] | None, Query()] = None,
    asset_id: str | None = None,
    source: str | None = None,
    ack: bool | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    session=Depends(get_db),
) -> EventsListResponse:
    del ack
    if to is not None and from_ts is not None and to <= from_ts:
        raise HTTPException(status_code=422, detail="to must be greater than from")
    decoded_cursor = None
    if cursor is not None:
        try:
            decoded_cursor = decode_cursor(cursor)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_CURSOR", "message": str(exc)},
            ) from exc

    result = await list_events(
        session,
        from_ts=from_ts,
        to_ts=to,
        event_names=event_name,
        severities=severity,
        asset_id=asset_id,
        source=source,
        cursor=decoded_cursor,
        limit=limit,
    )
    if result.items and any(item.params.get("reconstructed") for item in result.items):
        response.headers["X-Events-Reconstruction"] = "edge_only"
    return result


def _utc_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset().total_seconds() != 0:
        raise ValueError("cursor timestamp must be UTC")
    return value


