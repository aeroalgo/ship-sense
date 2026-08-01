from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.reports.models import ReportRun
from app.reports.schemas import ReportOutput, ReportPeriod, ReportProvenance


class ReportRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def next_version(self, report_id: UUID) -> int:
        result = await self._session.scalar(
            select(func.coalesce(func.max(ReportRun.version), 0) + 1).where(
                ReportRun.report_id == report_id
            )
        )
        return int(result or 1)

    async def insert_run(self, run: ReportRun) -> ReportRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def list_runs(
        self,
        *,
        report_type: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        limit: int = 50,
    ) -> list[ReportOutput]:
        query = select(ReportRun).order_by(ReportRun.generated_at.desc()).limit(limit)
        if report_type is not None:
            query = query.where(ReportRun.type == report_type)
        if from_ts is not None:
            query = query.where(ReportRun.generated_at >= from_ts)
        if to_ts is not None:
            query = query.where(ReportRun.generated_at < to_ts)
        result = await self._session.execute(query)
        return [_output_from_run(run) for run in result.scalars().all()]

    async def get_run(self, report_id: UUID, version: int | None = None) -> ReportOutput | None:
        query = select(ReportRun).where(ReportRun.report_id == report_id)
        if version is None:
            query = query.order_by(ReportRun.version.desc()).limit(1)
        else:
            query = query.where(ReportRun.version == version)
        result = await self._session.execute(query)
        run = result.scalars().first()
        return _output_from_run(run) if run is not None else None


def _output_from_run(run: ReportRun) -> ReportOutput:
    return ReportOutput(
        report_id=str(run.report_id),
        version=run.version,
        type=run.type,
        period=ReportPeriod.model_validate(
            {
                "from": run.period_from,
                "to": run.period_to,
                "boundary_rule": run.boundary_rule,
            }
        ),
        formulas_version=run.formulas_version,
        data_watermark=run.data_watermark,
        generated_at=run.generated_at,
        initiated_by=run.initiated_by,
        body_json=run.body_json,
        body_html=run.body_html,
        provenance=ReportProvenance.model_validate(run.provenance),
        status=run.status,
    )
