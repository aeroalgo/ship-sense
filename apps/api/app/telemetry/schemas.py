from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.telemetry.models import Quality

Resolution = Literal[
    "raw", "1s", "2s", "5s", "10s", "30s", "1m", "5m", "10m", "15m", "1h", "4h", "1d"
]
AggregateFunction = Literal["avg", "min", "max", "last"]


class SeriesPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ts: datetime
    value: float | int | bool | None
    quality: Quality = Field(..., examples=["quarantine"])
    min: float | None = None
    max: float | None = None
    samples: int = Field(ge=0)


class SeriesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag_id: str
    name: str
    unit: str
    from_ts: datetime = Field(alias="from")
    to: datetime
    resolution: Resolution
    points: list[SeriesPoint]


class AggregateSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag_id: str
    unit: str
    points: list[SeriesPoint]


class SeriesAggregateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_ts: datetime = Field(alias="from")
    to: datetime
    resolution: Resolution
    series: list[AggregateSeries]
