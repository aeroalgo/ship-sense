from __future__ import annotations

import random

from collector.core.restart_policy import RestartPolicy


def compute_backoff(attempt: int, policy: RestartPolicy) -> float:
    """Full-jitter exponential backoff (AWS decorrelated).

    expo = min(initial * 2**attempt, max). Без jitter → expo; с jitter →
    uniform(0, expo) — срез фазы (anti-thundering-herd при общей потере
    сети). Attempt клампится, чтобы 2**attempt не переполнял float
    (cap всё равно сработает раньше).
    """
    safe = min(attempt, 1023)  # 2.0**1023 ~ max double
    expo = min(
        policy.initial_backoff_sec * (2.0**safe), policy.max_backoff_sec
    )
    if not policy.jitter:
        return expo
    return random.uniform(0.0, expo)
