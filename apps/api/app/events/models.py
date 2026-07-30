from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.telemetry.models import Quality


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
