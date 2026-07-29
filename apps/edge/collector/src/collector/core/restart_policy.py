from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RestartPolicy:
    """Политика рестарта источника (plan §11.4).

    max_consecutive_failures=None → бесконечные попытки (default;
    edge-сервис сам себя лечит). При K → DOWN после K подряд неудач.
    """

    initial_backoff_sec: float = 1.0
    max_backoff_sec: float = 60.0
    max_consecutive_failures: int | None = None
    jitter: bool = True
