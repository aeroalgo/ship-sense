from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Quality(StrEnum):
    GOOD = "good"
    BAD = "bad"
    UNCERTAIN = "uncertain"
    STALE = "stale"
    QUARANTINE = "quarantine"


class RawSample(BaseModel):
    source_id: str = Field(..., description="ID из sources.yaml, напр. aps_main")
    native_id: str = Field(..., description="Адрес протокола: '40101' или 'ns=2;s=...'")
    raw_value: Any = Field(..., description="Декодированное значение до unit conversion")
    native_quality: str | None = Field(
        None, description="Сырой код: Modbus exception, OPC StatusCode name"
    )
    recv_ts: datetime = Field(..., description="UTC момент получения на edge (aware)")
    source_ts: datetime | None = Field(
        None, description="Timestamp от источника если протокол отдал"
    )
    sequence: int | None = Field(None, description="OPC UA sequence для dedup")


class RawTagDescriptor(BaseModel):
    native_id: str
    name: str | None = None
    unit: str | None = None
    datatype: str | None = None
    description: str | None = None


class TelemetrySample(BaseModel):
    tag_id: str = Field(..., description="KKS канонический, напр. TAI4101")
    value: float | int | bool | str | None
    unit: str = Field(..., description="Каноническая единица или 'unknown'")
    source_ts: datetime
    edge_ts: datetime
    quality: Quality
    source_id: str = Field(..., description="Происхождение для диагностики")
    native_id: str | None = Field(None, description="Опционально для ПНР trace")


class EventSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ALARM = "alarm"
    PROTECTION = "protection"


class Event(BaseModel):
    event_name: str = Field(..., description="Каноническое имя события")
    params: dict[str, Any] = Field(default_factory=dict)
    ts: datetime = Field(..., description="Момент события")
    edge_ts: datetime
    source: str = Field(..., description="source_id или 'edge'")
    tag_id: str | None = None
    severity: EventSeverity = EventSeverity.INFO
    idempotency_key: str = Field(..., description="Ключ дедупликации события")
    quality: Quality = Quality.GOOD


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
