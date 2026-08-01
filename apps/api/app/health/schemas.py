from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CheckStatus(BaseModel):
    status: str
    latency_ms: float | None = None
    last_sample_ts: datetime | None = None
    used_pct: float | None = None
    alert: bool | None = None
    path: str | None = None
    active_connections: int | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    uptime_sec: float
    checks: dict[str, CheckStatus]


class SourceStatus(BaseModel):
    source_id: str
    name: str
    connected: bool
    last_poll_ts: datetime | None = None
    error_count_24h: int = 0
    quality_summary: Literal["good", "uncertain", "bad", "stale", "quarantine"]
    tags_active: int = 0
    tags_quarantine: int = 0
    tags_stale: int = 0


class SourcesStatusResponse(BaseModel):
    items: list[SourceStatus]
