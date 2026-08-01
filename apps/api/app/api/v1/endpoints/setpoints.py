from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_db
from app.core.settings import settings
from app.setpoints.events import fetch_setpoint_changes
from app.setpoints.schemas import (
    SetpointChangelogResponse,
    SetpointHistoryResponse,
    SetpointsListResponse,
)
from app.setpoints.service import SetpointsService

router = APIRouter(tags=["setpoints"])


@router.get("/setpoints", response_model=SetpointsListResponse, operation_id="getSetpoints")
async def get_setpoints() -> SetpointsListResponse:
    return SetpointsService(settings.SHIP_PACK_PATH).list_all()


@router.get(
    "/setpoints/history",
    response_model=SetpointHistoryResponse,
    operation_id="getSetpointHistory",
)
async def get_setpoint_history(tag: str = Query(min_length=1)) -> SetpointHistoryResponse:
    try:
        return SetpointsService(settings.SHIP_PACK_PATH).history(tag)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TAG_NOT_FOUND", "message": f"Unknown tag: {exc.args[0]}"},
        ) from exc


@router.get(
    "/setpoints/changelog",
    response_model=SetpointChangelogResponse,
    operation_id="getSetpointChangelog",
)
async def get_setpoint_changelog(
    from_ts: Annotated[datetime | None, Query(alias="from")] = None,
    to: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 200,
    session=Depends(get_db),
) -> SetpointChangelogResponse:
    if from_ts is not None and from_ts.tzinfo is None:
        raise HTTPException(status_code=422, detail="from must include timezone")
    if to is not None and to.tzinfo is None:
        raise HTTPException(status_code=422, detail="to must include timezone")
    if from_ts is not None and to is not None and to < from_ts:
        raise HTTPException(status_code=422, detail="to must be greater than or equal to from")
    rows = await fetch_setpoint_changes(session, from_ts=from_ts, to_ts=to, limit=limit)
    return SetpointsService.changelog_rows(rows)
