from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.reports.models import ReportRun
from app.reports.schemas import ReportOutput, ReportProvenance, ReportRequest
from app.reports.templates import TemplateRenderer


class ReportEngine:
    def __init__(
        self,
        repository,
        *,
        watermark_provider: Callable[[ReportRequest], Awaitable[datetime]] | None = None,
    ) -> None:
        self._repository = repository
        self._watermark_provider = watermark_provider or self._default_watermark
        self._template_renderer = TemplateRenderer()

    async def generate(self, request: ReportRequest) -> ReportOutput:
        watermark = await self._watermark_provider(request)
        generated_at = datetime.now(timezone.utc)
        report_id = uuid4()
        version = await self._repository.next_version(report_id)
        status = "final" if watermark >= request.period.to else "preliminary"
        provenance = ReportProvenance(official_ts_rule=request.period.boundary_rule)
        body_json, body_html = self._template_renderer.render_report(
            request.type,
            {"period": request.period.model_dump(mode="json"), "provenance": provenance.model_dump(mode="json")},
        )
        run = ReportRun(
            report_id=report_id,
            version=version,
            type=request.type,
            period_from=request.period.from_,
            period_to=request.period.to,
            boundary_rule=request.period.boundary_rule,
            asset_scope=request.asset_scope,
            formulas_version=request.formulas_version,
            data_watermark=watermark,
            generated_at=generated_at,
            initiated_by=request.initiated_by,
            body_json=body_json,
            body_html=body_html,
            provenance=provenance.model_dump(mode="json"),
            status=status,
        )
        await self._repository.insert_run(run)
        return ReportOutput(
            report_id=str(report_id),
            version=version,
            type=request.type,
            period=request.period,
            formulas_version=request.formulas_version,
            data_watermark=watermark,
            generated_at=generated_at,
            initiated_by=request.initiated_by,
            body_json=body_json,
            body_html=body_html,
            provenance=provenance,
            status=status,
        )

    @staticmethod
    async def _default_watermark(_request: ReportRequest) -> datetime:
        return datetime.now(timezone.utc)
