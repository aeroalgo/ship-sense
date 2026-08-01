from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Any

from sqlalchemy import and_, select

from app.reports.schemas import (
    DataQuality,
    ReportCatalogItem,
    ReportHighlight,
    ReportTagSnapshot,
    ReportOutput,
    ReportSummary,
    ReportsListResponse,
    StaleInterval,
    Watchkeeper,
    WatchReportResponse,
)
from app.telemetry.models import Quality
from app.warnings.schemas import DriftWarning
from apps.edge.storage.schemas import Event as DBEvent, Sample as DBSample, TagQuarantine


_REPORT_DESCRIPTION = "Отчёт B12 с provenance и печатным представлением"
_REPORT_CATALOG = (
    ("watch", "Вахтенная сводка", "Реконструкция вахты по official timestamp"),
    ("daily_noon", "Полуденный отчёт", "Сводка суточных показателей"),
    ("fuel", "Отчёт по топливу", "Расход и остатки топлива"),
    ("register", "Реестр событий", "Реестр тревог и защит"),
)
_BANNER = "Часть периода под сверкой — см. quarantine_tags"
_SEVERITY = {0: "info", 1: "warning", 2: "alarm", 3: "protection", 4: "protection"}
_QUALITY = {
    0: Quality.GOOD,
    1: Quality.UNCERTAIN,
    2: Quality.BAD,
    3: Quality.STALE,
    4: Quality.QUARANTINE,
}
_SEVERITY_RANK = {"protection": 3, "alarm": 2, "warning": 1, "info": 0}


class ReportsService:
    @staticmethod
    def list_types() -> ReportsListResponse:
        return ReportsListResponse(
            items=[
                ReportCatalogItem(
                    type=report_type,
                    title=title,
                    formats=["json", "html"],
                    description=description,
                )
                for report_type, title, description in _REPORT_CATALOG
            ]
        )

    async def generate(self, session: Any, request: Any):
        from app.reports.engine import ReportEngine
        from app.reports.repository import ReportRunRepository

        if request.type == "watch":
            watch = await self.build_watch(session, request.period.from_, request.period.to)
            body_json = watch.model_dump(mode="json")
            body_html = render_html(watch)
            from app.reports.models import ReportRun
            from uuid import uuid4
            from datetime import datetime, timezone

            report_id = uuid4()
            generated_at = datetime.now(timezone.utc)
            run = ReportRun(
                report_id=report_id,
                version=1,
                type=request.type,
                period_from=request.period.from_,
                period_to=request.period.to,
                boundary_rule=request.period.boundary_rule,
                asset_scope=request.asset_scope,
                formulas_version=request.formulas_version,
                data_watermark=generated_at,
                generated_at=generated_at,
                initiated_by=request.initiated_by,
                body_json=body_json,
                body_html=body_html,
                provenance={"official_ts_rule": "official_ts"},
                status="final",
            )
            session.add(run)
            await session.flush()
            return ReportOutput(
                report_id=str(report_id), version=1, type=request.type, period=request.period,
                formulas_version=request.formulas_version, data_watermark=generated_at,
                generated_at=generated_at, initiated_by=request.initiated_by,
                body_json=body_json, body_html=body_html,
                provenance={"official_ts_rule": "official_ts"}, status="final",
            )
        return await ReportEngine(ReportRunRepository(session)).generate(request)

    async def list_runs(self, session: Any, **filters: Any):
        from app.reports.repository import ReportRunRepository

        return await ReportRunRepository(session).list_runs(**filters)

    async def get_run(self, session: Any, report_id: Any, version: int | None = None):
        from app.reports.repository import ReportRunRepository

        return await ReportRunRepository(session).get_run(report_id, version)

    @staticmethod
    def schedule(roster: Any) -> dict[str, Any]:
        items = roster.roster().items
        return {"items": [item.model_dump(mode="json") for item in items], "boundary_rule": "watch_explicit"}

    async def build_watch(
        self,
        session: Any,
        from_ts: datetime,
        to_ts: datetime,
        watchkeeper: Watchkeeper | None = None,
    ) -> WatchReportResponse:
        events = await self._load_events(session, from_ts, to_ts)
        samples = await self._load_samples(session, from_ts, to_ts)
        quarantine = await self._load_quarantine(session, from_ts, to_ts)
        drifts = await self._load_drifts(session, from_ts, to_ts)
        quarantine_tags = {str(row.tag_id) for row in quarantine}
        quarantine_tags.update(
            str(tag_id)
            for row in samples
            if _quality(row.quality) is Quality.QUARANTINE
            for tag_id in [row.tag_id]
        )
        stale_intervals = _stale_intervals(samples)
        data_quality = DataQuality(
            quarantine_tags=sorted(quarantine_tags),
            stale_intervals=stale_intervals,
            banner=_BANNER if quarantine_tags or stale_intervals else None,
        )
        summary = _summary(events, data_quality)
        return WatchReportResponse(
            generated_at=datetime.now(timezone.utc),
            watchkeeper=watchkeeper,
            period={"from": from_ts, "to": to_ts},
            data_quality=data_quality,
            summary=summary,
            highlights=_highlights(events),
            tags_snapshot=_tag_snapshot(samples),
            drifts=drifts,
        )

    async def _load_drifts(self, session: Any, from_ts: datetime, to_ts: datetime) -> list[DriftWarning]:
        from app.warnings.service import WarningService

        return await WarningService().overlapping(session, from_ts=from_ts, to_ts=to_ts)

    async def _load_events(self, session: Any, from_ts: datetime, to_ts: datetime) -> list[Any]:
        result = await session.execute(
            select(DBEvent)
            .where(and_(DBEvent.official_ts >= from_ts, DBEvent.official_ts < to_ts))
            .order_by(DBEvent.official_ts.asc(), DBEvent.event_id.asc())
        )
        return list(result.scalars().all())

    async def _load_samples(self, session: Any, from_ts: datetime, to_ts: datetime) -> list[Any]:
        result = await session.execute(
            select(DBSample)
            .where(and_(DBSample.official_ts >= from_ts, DBSample.official_ts < to_ts))
            .order_by(DBSample.official_ts.asc(), DBSample.tag_id.asc())
        )
        return list(result.scalars().all())

    async def _load_quarantine(self, session: Any, from_ts: datetime, to_ts: datetime) -> list[Any]:
        result = await session.execute(
            select(TagQuarantine)
            .where(and_(TagQuarantine.since < to_ts, TagQuarantine.since >= from_ts))
            .order_by(TagQuarantine.tag_id.asc())
        )
        return list(result.scalars().all())


def _quality(value: int) -> Quality:
    return _QUALITY.get(value, Quality.UNCERTAIN)


def _summary(events: list[Any], quality: DataQuality) -> ReportSummary:
    protections = [event for event in events if _event_severity(event) == "protection" or _is_protection(event)]
    alarms = [event for event in events if _event_severity(event) == "alarm"]
    warnings = [event for event in events if _event_severity(event) == "warning"]
    if protections:
        verdict = f"Критический режим: зафиксированы срабатывания защит ({len(protections)})"
    elif alarms:
        verdict = f"Были тревоги: {len(alarms)}"
    elif warnings:
        verdict = f"Есть предупреждения: {len(warnings)}"
    else:
        verdict = "Тревог и срабатываний защит не зафиксировано"
    if quality.banner:
        verdict += ". Данные частично под сверкой"
    return ReportSummary(
        events_count=len(events),
        alarms_count=len(alarms),
        protections_count=len(protections),
        verdict=verdict,
    )


def _event_severity(event: Any) -> str:
    return _SEVERITY.get(event.severity, "info")


def _is_protection(event: Any) -> bool:
    name = str(event.event_name).lower()
    return name.startswith(("protection.", "trip."))


def _highlights(events: list[Any]) -> list[ReportHighlight]:
    groups: list[dict[str, Any]] = []
    for event in events:
        severity = _event_severity(event)
        if severity not in {"warning", "alarm", "protection"} and not _is_protection(event):
            continue
        params = dict(event.params or {})
        asset_id = params.get("asset_id")
        kks = params.get("kks")
        key = (event.event_name, asset_id, kks)
        if groups and groups[-1]["key"] == key and event.official_ts - groups[-1]["last_ts"] <= timedelta(seconds=60):
            groups[-1]["last_ts"] = event.official_ts
            groups[-1]["count"] += 1
            if _SEVERITY_RANK[severity] > _SEVERITY_RANK[groups[-1]["severity"]]:
                groups[-1]["severity"] = severity
            continue
        groups.append(
            {
                "key": key,
                "id": str(event.event_id),
                "ts": event.official_ts,
                "first_ts": event.official_ts,
                "last_ts": event.official_ts,
                "event_name": event.event_name,
                "severity": "protection" if _is_protection(event) else severity,
                "source": event.source,
                "asset_id": asset_id,
                "kks": kks,
                "count": 1,
                "params": params,
            }
        )
    groups.sort(key=lambda item: (-_SEVERITY_RANK[item["severity"]], -item["last_ts"].timestamp(), str(item["key"])))
    return [ReportHighlight(**{key: value for key, value in item.items() if key != "key"}) for item in groups[:5]]


def _stale_intervals(samples: list[Any]) -> list[StaleInterval]:
    stale = sorted(row.official_ts for row in samples if _quality(row.quality) is Quality.STALE)
    if not stale:
        return []
    intervals: list[tuple[datetime, datetime]] = []
    for timestamp in stale:
        interval = (timestamp, timestamp)
        if intervals and timestamp - intervals[-1][1] <= timedelta(seconds=1):
            intervals[-1] = (intervals[-1][0], timestamp)
        else:
            intervals.append(interval)
    return [StaleInterval.model_validate({"from": start, "to": end}) for start, end in intervals]


def _tag_snapshot(samples: list[Any]) -> list[ReportTagSnapshot]:
    grouped: dict[str, list[Any]] = defaultdict(list)
    for row in samples:
        if row.value is not None:
            grouped[row.tag_id].append(row)
    result = []
    for tag_id, rows in grouped.items():
        values = [float(row.value) for row in rows]
        worst = max((_quality(row.quality) for row in rows), key=lambda quality: list(_QUALITY.values()).index(quality))
        result.append(ReportTagSnapshot(tag_id=tag_id, name=tag_id, avg=sum(values) / len(values), min=min(values), max=max(values), quality_worst=worst))
    return sorted(result, key=lambda item: (-len(grouped[item.tag_id]), item.tag_id))[:3]


def render_html(report: WatchReportResponse) -> str:
    def dt(value: datetime) -> str:
        return escape(value.isoformat().replace("+00:00", "Z"))

    rows = "".join(
        f"<tr><td>{escape(item.tag_id)}</td><td>{item.avg:.2f}</td><td>{item.min:.2f}</td><td>{item.max:.2f}</td><td>{escape(item.quality_worst.value)}</td></tr>"
        for item in report.tags_snapshot
    )
    highlights = "".join(
        f"<li>{escape(item.event_name)} — {escape(item.asset_id or '')} ({escape(item.severity)})</li>"
        for item in report.highlights
    )
    banner = f"<p class=\"quality-banner\">{escape(report.data_quality.banner)}</p>" if report.data_quality.banner else ""
    return f"""<!doctype html>
<html lang=\"ru\"><head><meta charset=\"utf-8\"><title>Вахтенная сводка</title>
<style>@media print {{ body {{ font-family: sans-serif; }} }} .quality-banner {{ border: 1px solid #b45309; padding: 8px; }}</style></head>
<body><main><h1>Вахтенная сводка</h1><p>Период: {dt(report.period['from'])} — {dt(report.period['to'])}</p>
<h2>{escape(report.summary.verdict)}</h2>{banner}<h3>События</h3><ul>{highlights}</ul>
<table><thead><tr><th>Tag</th><th>Avg</th><th>Min</th><th>Max</th><th>Quality</th></tr></thead><tbody>{rows}</tbody></table></main></body></html>"""
