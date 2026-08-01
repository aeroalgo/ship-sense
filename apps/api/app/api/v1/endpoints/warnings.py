from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_db
from app.warnings.schemas import (
    WarningHistoryResponse,
    WarningStatus,
    WarningsListResponse,
)
from app.warnings.service import WarningService


router = APIRouter(tags=["warnings"])


@router.get("/warnings", response_model=WarningsListResponse, operation_id="getWarnings")
async def get_warnings(
    active: bool | None = None,
    tag_id: str | None = Query(default=None, min_length=1),
    asset_id: str | None = Query(default=None, min_length=1),
    since: datetime | None = None,
    session=Depends(get_db),
) -> WarningsListResponse:
    items = await WarningService().list_active(
        session, active=active, tag_id=tag_id, asset_id=asset_id, since=since
    )
    return WarningsListResponse(items=items)


@router.get(
    "/warnings/history",
    response_model=WarningHistoryResponse,
    operation_id="getWarningsHistory",
)
async def get_warnings_history(
    tag_id: str | None = Query(default=None, min_length=1),
    asset_id: str | None = Query(default=None, min_length=1),
    since: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session=Depends(get_db),
) -> WarningHistoryResponse:
    items, has_more = await WarningService().history(
        session,
        tag_id=tag_id,
        asset_id=asset_id,
        since=since,
        limit=limit,
        offset=offset,
    )
    return WarningHistoryResponse(
        items=items,
        limit=limit,
        offset=offset,
        has_more=has_more,
        next_offset=offset + limit if has_more else None,
    )
