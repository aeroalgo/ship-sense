from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class SourceState(StrEnum):
    UP = "up"
    RECONNECTING = "reconnecting"
    DOWN = "down"
    DEGRADED = "degraded"


class HealthStatus(BaseModel):
    source_id: str
    state: SourceState
    last_ok_ts: datetime | None = None
    reconnect_count: int = 0
    detail: str | None = None
    tags_total: int = 0
    tags_active: int = 0
    sample_rate_hz: float | None = None
    protocol: str | None = None
    connected: bool | None = None
    subscribed: bool | None = None
    last_msg_ts: datetime | None = None
    parse_errors: int | None = None
    broker_reachable: bool | None = None


class CollectorHealthSnapshot(BaseModel):
    ts: datetime
    collector_state: str
    sources: list[HealthStatus]
    queue_raw_depth: int
    queue_canonical_depth: int
    samples_total: int
    events_total: int
    errors_total: int
