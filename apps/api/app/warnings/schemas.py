from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.telemetry.models import Quality


class WarningStatus(StrEnum):
    ACTIVE = "active"
    CLEARED = "cleared"


class DriftWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag_id: str
    asset_id: str | None = None
    status: WarningStatus
    raw_value: float
    ewma_value: float
    setpoint: float
    setpoint_source: str
    unit: str
    threshold_pct: float = Field(gt=0, lt=1)
    comparison: str
    slope_per_hour: float | None = None
    eta_to_setpoint_days: float | None = None
    quality: Quality = Quality.GOOD
    suppressed_reason: str | None = None
    since: datetime
    config_version: str


class WarningTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag_id: str
    from_status: WarningStatus
    to_status: WarningStatus
    occurred_at: datetime
    warning: DriftWarning


class WarningsListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DriftWarning]


class WarningHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[WarningTransition]
    limit: int
    offset: int
    has_more: bool
    next_offset: int | None = None
