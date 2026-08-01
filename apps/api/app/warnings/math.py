from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from math import exp


@dataclass(frozen=True)
class EwmaState:
    value: float
    timestamp: datetime


def ewma_update(
    previous: EwmaState | None,
    value: float,
    timestamp: datetime,
    *,
    tau: float,
) -> EwmaState:
    if tau <= 0:
        raise ValueError("tau must be positive")
    if previous is None:
        return EwmaState(value=float(value), timestamp=timestamp)
    dt = (timestamp - previous.timestamp).total_seconds()
    if dt < 0:
        raise ValueError("timestamp must not move backwards")
    if dt == 0:
        return previous
    alpha = 1.0 - exp(-dt / tau)
    return EwmaState(
        value=alpha * float(value) + (1.0 - alpha) * previous.value,
        timestamp=timestamp,
    )


def drift_rate(points: Sequence[tuple[float, float]]) -> float | None:
    if len(points) < 2:
        return None
    mean_x = sum(point[0] for point in points) / len(points)
    mean_y = sum(point[1] for point in points) / len(points)
    denominator = sum((x - mean_x) ** 2 for x, _ in points)
    if denominator == 0:
        return None
    return sum((x - mean_x) * (y - mean_y) for x, y in points) / denominator


def eta_days(current: float, setpoint: float, slope_per_hour: float | None) -> float | None:
    if slope_per_hour is None or slope_per_hour <= 0 or current >= setpoint:
        return None
    return (setpoint - current) / slope_per_hour / 24.0
