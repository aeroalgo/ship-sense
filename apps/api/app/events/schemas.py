from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.events.models import EventSeverity


class EventItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    ts: datetime
    event_name: str
    severity: EventSeverity | None
    source: str
    asset_id: str | None
    params: dict[str, Any]
    quality: str | None


class EventsListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[EventItem]
    next_cursor: str | None
    has_more: bool
