from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SetpointItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag_id: str
    value: float
    unit: str
    label: str
    effective_from: datetime


class SetpointsListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SetpointItem]


class Segment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_ts: datetime
    to_ts: datetime | None = None
    value: float


class SetpointHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag_id: str
    segments: list[Segment]


class SetpointChangelogItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    ts: datetime
    tag_id: str
    old_value: float
    new_value: float
    unit: str
    source: str
    actor: str | None = None


class SetpointChangelogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SetpointChangelogItem]
