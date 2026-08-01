from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.warnings.math import EwmaState, drift_rate, eta_days, ewma_update


class WarningState(StrEnum):
    CLEAR = "clear"
    ACTIVE = "active"
    SUPPRESSED = "suppressed"


@dataclass(frozen=True)
class DriftSample:
    timestamp: datetime
    value: float
    rpm: float | None = None


@dataclass(frozen=True)
class DriftResult:
    tag_id: str
    state: WarningState
    raw_value: float
    ewma_value: float
    setpoint: float
    slope_per_hour: float | None = None
    eta_to_setpoint_days: float | None = None
    suppressed_reason: str | None = None


@dataclass
class DriftEngine:
    tag_id: str
    setpoint: float
    threshold_pct: float = 0.9
    hysteresis_pct: float = 0.02
    ewma_window_hours: float = 24.0
    min_trend_len: int = 2
    startup_guard_sec: float = 300.0
    rpm_min: float = 10.0
    _ewma: EwmaState | None = field(default=None, init=False)
    _points: list[tuple[float, float]] = field(default_factory=list, init=False)
    _state: WarningState = field(default=WarningState.CLEAR, init=False)
    _running_since: datetime | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.setpoint <= 0:
            raise ValueError("setpoint must be positive")
        if not 0 < self.threshold_pct < 1:
            raise ValueError("threshold_pct must be between 0 and 1")
        if not 0 <= self.hysteresis_pct < self.threshold_pct:
            raise ValueError("hysteresis_pct must be below threshold_pct")
        if self.ewma_window_hours <= 0:
            raise ValueError("ewma_window_hours must be positive")
        if self.min_trend_len < 2:
            raise ValueError("min_trend_len must be at least 2")

    def process(self, sample: DriftSample) -> DriftResult:
        if self._running_since is None and sample.rpm is not None and sample.rpm >= self.rpm_min:
            self._running_since = sample.timestamp
        if sample.rpm is not None and sample.rpm < self.rpm_min:
            self._state = WarningState.SUPPRESSED
            return self._result(sample, "low_rpm")
        if self._running_since is None or (
            sample.timestamp - self._running_since
        ).total_seconds() < self.startup_guard_sec:
            self._state = WarningState.SUPPRESSED
            return self._result(sample, "startup_guard")

        self._ewma = ewma_update(
            self._ewma,
            sample.value,
            sample.timestamp,
            tau=self.ewma_window_hours * 3600.0,
        )
        now_seconds = sample.timestamp.timestamp()
        window_seconds = self.ewma_window_hours * 3600.0
        self._points.append((now_seconds, self._ewma.value))
        self._points = [point for point in self._points if now_seconds - point[0] <= window_seconds]
        slope_per_second = drift_rate(self._points) if len(self._points) >= self.min_trend_len else None
        slope_per_hour = slope_per_second * 3600.0 if slope_per_second is not None else None

        if self._state is WarningState.SUPPRESSED:
            self._state = WarningState.CLEAR
        enter_level = self.setpoint * self.threshold_pct
        exit_level = self.setpoint * (self.threshold_pct - self.hysteresis_pct)
        if self._state is WarningState.ACTIVE:
            if self._ewma.value < exit_level:
                self._state = WarningState.CLEAR
        elif self._ewma.value >= enter_level:
            self._state = WarningState.ACTIVE

        return DriftResult(
            tag_id=self.tag_id,
            state=self._state,
            raw_value=sample.value,
            ewma_value=self._ewma.value,
            setpoint=self.setpoint,
            slope_per_hour=slope_per_hour,
            eta_to_setpoint_days=eta_days(self._ewma.value, self.setpoint, slope_per_hour),
        )

    def _result(self, sample: DriftSample, reason: str) -> DriftResult:
        ewma_value = self._ewma.value if self._ewma is not None else sample.value
        return DriftResult(
            tag_id=self.tag_id,
            state=self._state,
            raw_value=sample.value,
            ewma_value=ewma_value,
            setpoint=self.setpoint,
            suppressed_reason=reason,
        )
