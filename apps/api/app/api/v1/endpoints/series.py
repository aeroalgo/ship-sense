from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_db, get_semantic_engine
from app.core.settings import settings
from app.semantic.engine import SemanticEngine
from app.telemetry.schemas import AggregateFunction, SeriesAggregateResponse, SeriesResponse
from app.telemetry.service import DownsampleService

router = APIRouter(tags=["series"])


@router.get("/series", response_model=SeriesResponse, operation_id="getSeries")
async def get_series(
    tag: str,
    from_ts: Annotated[datetime, Query(alias="from")],
    to: datetime,
    resolution: str = "auto",
    session=Depends(get_db),
    engine: SemanticEngine = Depends(get_semantic_engine),
) -> SeriesResponse:
    _validate_window(from_ts, to)
    try:
        return await DownsampleService(session, engine).fetch_series(
            tag, from_ts, to, resolution
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TAG_NOT_FOUND", "message": f"Unknown tag: {exc.args[0]}"},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/series/aggregate",
    response_model=SeriesAggregateResponse,
    operation_id="getSeriesAggregate",
)
async def get_series_aggregate(
    tags: Annotated[list[str], Query(min_length=1)],
    from_ts: Annotated[datetime, Query(alias="from")],
    to: datetime,
    resolution: str = "auto",
    fn: AggregateFunction = "avg",
    session=Depends(get_db),
    engine: SemanticEngine = Depends(get_semantic_engine),
) -> SeriesAggregateResponse:
    _validate_window(from_ts, to)
    try:
        return await DownsampleService(session, engine).fetch_aggregate(
            tags, from_ts, to, resolution, fn
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TAG_NOT_FOUND", "message": f"Unknown tag: {exc.args[0]}"},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _validate_window(from_ts: datetime, to: datetime) -> None:
    if to <= from_ts:
        raise HTTPException(status_code=422, detail="to must be greater than from")
    if (to - from_ts).total_seconds() > settings.API_SERIES_MAX_WINDOW_DAYS * 86_400:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "WINDOW_TOO_LARGE",
                "message": "Series window exceeds the configured maximum",
            },
        )
