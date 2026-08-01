from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.telemetry.models import Quality


class ReportCatalogItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    title: str
    formats: list[str]
    description: str


class ReportsListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ReportCatalogItem]


class StaleInterval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_ts: datetime = Field(alias="from")
    to_ts: datetime = Field(alias="to")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class DataQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quarantine_tags: list[str]
    stale_intervals: list[StaleInterval]
    banner: str | None


class Watchkeeper(BaseModel):
    model_config = ConfigDict(extra="forbid")

    person_id: str
    name: str
    rank: str


class ReportSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    events_count: int
    alarms_count: int
    protections_count: int
    verdict: str


class ReportHighlight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    ts: datetime
    event_name: str
    severity: str
    source: str
    asset_id: str | None
    kks: str | None
    first_ts: datetime
    last_ts: datetime
    count: int
    params: dict[str, object]


class ReportTagSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag_id: str
    name: str
    avg: float
    min: float
    max: float
    quality_worst: Quality


class WatchReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    watchkeeper: Watchkeeper | None
    period: dict[str, datetime]
    data_quality: DataQuality
    summary: ReportSummary
    highlights: list[ReportHighlight]
    tags_snapshot: list[ReportTagSnapshot]


ReportFormat = Literal["json", "html"]
ReportType = Literal["watch", "daily_noon", "fuel", "register"]
BoundaryRule = Literal["watch_explicit", "vessel_day_noon", "calendar_utc", "custom"]
ReportStatus = Literal["final", "preliminary"]


class ReportPeriod(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_: datetime = Field(alias="from")
    to: datetime
    boundary_rule: BoundaryRule

    @property
    def from_ts(self) -> datetime:
        return self.from_


class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ReportType
    period: ReportPeriod
    asset_scope: str | None = None
    formulas_version: str = "latest"
    initiated_by: str | None = None


class ReportProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quarantined_tags: list[str] = Field(default_factory=list)
    stale_intervals: list[StaleInterval] = Field(default_factory=list)
    gaps: list[StaleInterval] = Field(default_factory=list)
    official_ts_rule: str


class ReportOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    version: int
    type: ReportType
    period: ReportPeriod
    formulas_version: str
    data_watermark: datetime
    generated_at: datetime
    initiated_by: str | None = None
    body_json: dict[str, object] = Field(default_factory=dict)
    body_html: str | None = None
    provenance: ReportProvenance
    status: ReportStatus
    immutable: bool = True
