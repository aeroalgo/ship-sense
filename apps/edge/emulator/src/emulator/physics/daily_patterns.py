from __future__ import annotations

import math

DAY_SECONDS = 24 * 60 * 60


def daily_factor(seconds: int | float, *, period: float = DAY_SECONDS, amplitude: float = 0.5, phase: float = 0.0) -> float:
    """Return a bounded, timezone-free periodic factor in [0, 1]."""
    if period <= 0:
        raise ValueError("period must be positive")
    if not 0 <= amplitude <= 1:
        raise ValueError("amplitude must be between 0 and 1")
    return 0.5 + amplitude / 2 * math.sin(2 * math.pi * (seconds / period) + phase)
