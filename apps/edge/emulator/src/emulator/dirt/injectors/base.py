from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class InjectorContext:
    seed: int
    tick_hz: float


@dataclass
class BaseInjector:
    """Shared timing and signal-selection behavior for scenario injectors."""

    params: Mapping[str, Any] = field(default_factory=dict)
    context: InjectorContext = field(default_factory=lambda: InjectorContext(0, 1.0))

    @property
    def at_sec(self) -> float:
        return float(self.params.get("at_sec", 0.0))

    @property
    def duration_sec(self) -> float | None:
        duration = self.params.get("duration_sec")
        return None if duration is None else float(duration)

    def is_active(self, elapsed_sec: float) -> bool:
        if elapsed_sec < self.at_sec:
            return False
        duration = self.duration_sec
        return duration is None or elapsed_sec < self.at_sec + duration

    def selected(self, signal_id: str) -> bool:
        selectors = self.params.get("signal_ids", self.params.get("tag_ids", self.params.get("tag_id")))
        if selectors is None:
            return True
        if isinstance(selectors, str):
            return signal_id == selectors
        return signal_id in selectors

    def native_ids(self, signal: Mapping[str, Any]) -> tuple[str, ...]:
        return tuple(str(value) for value in signal.get("native_ids", {}).values())
