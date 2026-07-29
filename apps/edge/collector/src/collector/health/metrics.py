"""Metrics counters for collector health (AC-HLT-03)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Metrics:
    """Глобальные счётчики collector (не per-source).

    Per-source метрики (uptime, reconnects, last_ok_ts, sample_rate) — в HealthStatus
    источника (domain/models.py). Здесь — aggregate counters + queue depths.

    Queue depths — внешние: ставятся через set_queue_depths() из RawConsumer/QueueSink.
    """

    samples_in: int = 0
    samples_out: int = 0
    errors: int = 0
    queue_raw_depth: int = 0
    queue_canonical_depth: int = 0

    def bump_samples_in(self, delta: int = 1) -> None:
        self.samples_in += delta

    def bump_samples_out(self, delta: int = 1) -> None:
        self.samples_out += delta

    def bump_errors(self, delta: int = 1) -> None:
        self.errors += delta

    def set_queue_depths(self, *, raw: int, canonical: int) -> None:
        self.queue_raw_depth = raw
        self.queue_canonical_depth = canonical
