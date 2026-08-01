from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from uuid import uuid4

from app.reports.schemas import ReportGenerateRequest, ReportJob, ReportOutput


class ReportJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, ReportJob] = {}

    def create(
        self,
        request: ReportGenerateRequest,
        generate: Callable[[ReportGenerateRequest], Awaitable[ReportOutput]],
    ) -> ReportJob:
        job = ReportJob(job_id=str(uuid4()), status="queued")
        self._jobs[job.job_id] = job
        asyncio.create_task(self._run(job.job_id, request, generate))
        return job

    def get(self, job_id: str) -> ReportJob | None:
        return self._jobs.get(job_id)

    async def _run(
        self,
        job_id: str,
        request: ReportGenerateRequest,
        generate: Callable[[ReportGenerateRequest], Awaitable[ReportOutput]],
    ) -> None:
        self._jobs[job_id] = self._jobs[job_id].model_copy(update={"status": "running"})
        try:
            report = await generate(request)
        except Exception as exc:
            self._jobs[job_id] = self._jobs[job_id].model_copy(
                update={"status": "failed", "error": str(exc)}
            )
        else:
            self._jobs[job_id] = self._jobs[job_id].model_copy(
                update={"status": "done", "report": report}
            )


job_store = ReportJobStore()
