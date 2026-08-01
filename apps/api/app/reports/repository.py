from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.reports.models import ReportRun


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
