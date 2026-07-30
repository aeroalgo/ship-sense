from __future__ import annotations

from datetime import datetime
from typing import Any

from app.events.models import Event, EventSeverity
from app.telemetry.models import Quality


DiscreteKey = tuple[str, str]


class EventDetector:
    """Minimal Q4 detector: emit an event on discrete value changes."""

    def __init__(self) -> None:
        self._previous: dict[DiscreteKey, Any] = {}

    def detect(
        self,
        *,
        tag_id: str,
        value: Any,
        ts: datetime,
        edge_ts: datetime,
        source: str,
        quality: Quality,
        discrete: bool,
    ) -> Event | None:
        key = (source, tag_id)
        if not discrete or quality in (Quality.BAD, Quality.QUARANTINE):
            return None
        if key not in self._previous:
            self._previous[key] = value
            return None
        previous = self._previous[key]
        self._previous[key] = value
        if previous == value:
            return None
        return Event(
            event_name="discrete.changed",
            params={"from": previous, "to": value},
            ts=ts,
            edge_ts=edge_ts,
            source=source,
            tag_id=tag_id,
            severity=EventSeverity.INFO,
            idempotency_key=f"tag_changed:{source}:{tag_id}:{ts.isoformat()}",
            quality=quality,
        )
