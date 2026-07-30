from __future__ import annotations

from app.events.models import Event
from app.telemetry.models import TelemetrySample


class NullSink:
    """Pure drop. Для тестов и dev-заглушек (CanonicalSink contract)."""

    async def write_sample(self, sample: TelemetrySample) -> None:
        return None

    async def write_event(self, event: Event) -> None:
        return None
