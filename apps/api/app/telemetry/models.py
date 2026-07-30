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


class TelemetrySample(BaseModel):
    tag_id: str = Field(..., description="KKS канонический, напр. TAI4101")
    value: float | int | bool | str | None
    unit: str = Field(..., description="Каноническая единица или 'unknown'")
    source_ts: datetime
    edge_ts: datetime
    quality: Quality
    source_id: str = Field(..., description="Происхождение для диагностики")
    native_id: str | None = Field(None, description="Опционально для ПНР trace")
