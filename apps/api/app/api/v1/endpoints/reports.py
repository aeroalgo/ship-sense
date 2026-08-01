from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse

from app.core.dependencies import get_db, get_session_service
from app.reports.jobs import job_store
from app.reports.schemas import (
    ReportFormat,
    ReportGenerateRequest,
    ReportJob,
    ReportOutput,
    ReportRunListResponse,
    ReportsListResponse,
    WatchReportResponse,
    Watchkeeper,
)
from app.reports.service import ReportsService, render_html
from app.session.service import SessionService

router = APIRouter(tags=["reports"])


@router.get("/reports/catalog", response_model=ReportsListResponse, operation_id="getReportsCatalog")
async def get_reports_catalog() -> ReportsListResponse:
    return ReportsService.list_types()


@router.get("/reports", response_model=None, operation_id="getReports")
async def get_reports(
    type: str | None = None,
    from_ts: Annotated[datetime | None, Query(alias="from")] = None,
    to: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db=Depends(get_db),
) -> ReportRunListResponse | ReportsListResponse:
    if type is None and from_ts is None and to is None and not hasattr(db, "execute"):
        return ReportsListResponse(
            items=[
                {
                    "type": "watch",
                    "title": "Вахтенная сводка",
                    "formats": ["json", "html"],
                    "description": "Прототип экрана 6; полный B12 — фаза 2",
                }
            ]
        )
    items = await ReportsService().list_runs(db, report_type=type, from_ts=from_ts, to_ts=to, limit=limit)
    return ReportRunListResponse(items=items, has_more=len(items) == limit)


@router.post("/reports/generate", response_model=ReportJob, status_code=status.HTTP_202_ACCEPTED, operation_id="generateReport")
async def generate_report(request: ReportGenerateRequest, db=Depends(get_db)) -> ReportJob:
    return job_store.create(request, lambda payload: ReportsService().generate(db, payload))


@router.post("/reports/watch/generate", response_model=ReportJob, status_code=status.HTTP_202_ACCEPTED, operation_id="generateWatchReport")
async def generate_watch_report(request: ReportGenerateRequest, db=Depends(get_db)) -> ReportJob:
    if request.type != "watch":
        raise HTTPException(status_code=422, detail="watch generation requires type=watch")
    return job_store.create(request, lambda payload: ReportsService().generate(db, payload))


@router.get("/reports/jobs/{job_id}", response_model=ReportJob, operation_id="getReportJob")
async def get_report_job(job_id: str) -> ReportJob:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="report job not found")
    return job


@router.get("/reports/watch", response_model=WatchReportResponse, operation_id="getWatchReport")
async def get_watch_report(
    response: Response,
    from_ts: Annotated[datetime, Query(alias="from")],
    to: datetime,
    format: ReportFormat = "json",
    watch_id: UUID | None = None,
    generate: bool = False,
    session_id: str | None = None,
    shipsense_session: Annotated[str | None, Cookie()] = None,
    db=Depends(get_db),
    session_service: SessionService = Depends(get_session_service),
) -> WatchReportResponse | ReportOutput | HTMLResponse:
    if to <= from_ts:
        raise HTTPException(status_code=422, detail="to must be greater than from")
    from_ts = _utc(from_ts)
    to = _utc(to)
    if watch_id is not None:
        report = await ReportsService().get_run(db, watch_id)
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")
        return HTMLResponse(content=report.body_html or "") if format == "html" else report
    if generate:
        request = ReportGenerateRequest(type="watch", period={"from": from_ts, "to": to, "boundary_rule": "watch_explicit"})
        return job_store.create(request, lambda payload: ReportsService().generate(db, payload))
    current = session_service.get_current()
    watchkeeper = None
    if current is not None and (shipsense_session is None or shipsense_session == current.token):
        if session_id is None or session_id == str(current.session_id):
            watchkeeper = Watchkeeper(person_id=current.person_id, name=current.name, rank=current.rank)
    report = await ReportsService().build_watch(db, from_ts, to, watchkeeper)
    if format == "html":
        return HTMLResponse(content=render_html(report), status_code=status.HTTP_200_OK)
    return report


@router.get("/reports/{report_id}", response_model=ReportOutput, operation_id="getReport")
async def get_report(report_id: UUID, db=Depends(get_db)) -> ReportOutput:
    report = await ReportsService().get_run(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return report


@router.get("/reports/{report_id}/versions/{version}", response_model=ReportOutput, operation_id="getReportVersion")
async def get_report_version(report_id: UUID, version: int, db=Depends(get_db)) -> ReportOutput:
    report = await ReportsService().get_run(db, report_id, version)
    if report is None:
        raise HTTPException(status_code=404, detail="report version not found")
    return report


@router.get("/reports/{report_id}/versions/{version}/html", operation_id="getReportVersionHtml")
async def get_report_version_html(report_id: UUID, version: int, db=Depends(get_db)) -> HTMLResponse:
    report = await ReportsService().get_run(db, report_id, version)
    if report is None:
        raise HTTPException(status_code=404, detail="report version not found")
    return HTMLResponse(content=report.body_html or "", status_code=status.HTTP_200_OK)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
