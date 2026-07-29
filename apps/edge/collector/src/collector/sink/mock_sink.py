from __future__ import annotations

from collector.domain.models import Event, TelemetrySample


class MockSink:
    """Счётчики для тестов (CanonicalSink contract)."""

    def __init__(self) -> None:
        self.samples = 0
        self.events = 0
        self.sample_history: list[TelemetrySample] = []
        self.event_history: list[Event] = []
        self.last_sample: TelemetrySample | None = None
        self.last_event: Event | None = None

    async def write_sample(self, sample: TelemetrySample) -> None:
        self.samples += 1
        self.sample_history.append(sample)
        self.last_sample = sample

    async def write_event(self, event: Event) -> None:
        self.events += 1
        self.event_history.append(event)
        self.last_event = event
