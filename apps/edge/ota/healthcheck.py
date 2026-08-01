from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

HealthSignalState = Literal["pass", "fail", "unknown"]


@dataclass(frozen=True, slots=True)
class HealthSignal:
    name: str
    state: HealthSignalState


@dataclass(frozen=True, slots=True)
class HealthStatus:
    last_sample_at: datetime | None
    signals: list[HealthSignal]


@dataclass(frozen=True, slots=True)
class HealthDecision:
    ready: bool
    consecutive_passes: int
    code: str


def evaluate_health(
    status: HealthStatus,
    *,
    now: datetime | None = None,
    consecutive_passes: int = 0,
    max_sample_age_seconds: float = 60.0,
    required_passes: int = 3,
) -> HealthDecision:
    current = now or datetime.now(timezone.utc)
    sample = status.last_sample_at
    if sample is None or sample.tzinfo is None:
        return HealthDecision(False, 0, "HEALTH_UNKNOWN")
    age = (current - sample).total_seconds()
    if age < 0 or age >= max_sample_age_seconds:
        return HealthDecision(False, 0, "STALE_SAMPLE")
    if any(signal.state == "unknown" for signal in status.signals):
        return HealthDecision(False, 0, "HEALTH_UNKNOWN")
    if any(signal.state == "fail" for signal in status.signals):
        return HealthDecision(False, 0, "HEALTH_FAIL")
    passed = consecutive_passes + 1
    return HealthDecision(passed >= required_passes, passed, "HEALTH_OK" if passed >= required_passes else "HEALTH_PENDING")
