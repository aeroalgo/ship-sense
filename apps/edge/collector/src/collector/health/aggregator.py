"""HealthAggregator — per-source + global health snapshot (AC-B1-07, AC-B1-12)."""

from __future__ import annotations

from datetime import datetime, timezone

from collector.domain.models import CollectorHealthSnapshot, HealthStatus
from collector.health.metrics import Metrics


class HealthAggregator:
    """Агрегат health статусов источников + глобальные счётчики.

    - update_source(status): перезаписывает статус по source_id
    - bump_*/set_queue_depths: делегируют в Metrics
    - snapshot(collector_state): собирает CollectorHealthSnapshot (UTC ts)
    - stop(): безопасный no-op (идемпотентен, для CollectorApp lifecycle)

    Не хранит события (events_total всегда 0 в этом шаге — B4 ещё нет).
    MQTT (AC-MQTT-40): protocol=mqtt требует subscribed/last_msg_ts/parse_errors
    (+ connected, broker_reachable).
    """

    def __init__(self) -> None:
        self._sources: dict[str, HealthStatus] = {}
        self._metrics = Metrics()

    def update_source(self, status: HealthStatus) -> None:
        self._sources[status.source_id] = self._merge_mqtt_source(status)

    @staticmethod
    def _merge_mqtt_source(status: HealthStatus) -> HealthStatus:
        if status.protocol != "mqtt":
            return status
        missing = [
            name
            for name in (
                "connected",
                "subscribed",
                "parse_errors",
                "broker_reachable",
            )
            if getattr(status, name) is None
        ]
        if missing:
            raise ValueError(
                f"mqtt health for {status.source_id} missing: {missing}"
            )
        return status

    def bump_samples_in(self, delta: int = 1) -> None:
        self._metrics.bump_samples_in(delta)

    def bump_samples_out(self, delta: int = 1) -> None:
        self._metrics.bump_samples_out(delta)

    def bump_errors(self, delta: int = 1) -> None:
        self._metrics.bump_errors(delta)

    def set_queue_depths(self, *, raw: int, canonical: int) -> None:
        self._metrics.set_queue_depths(raw=raw, canonical=canonical)

    def snapshot(self, collector_state: str) -> CollectorHealthSnapshot:
        return CollectorHealthSnapshot(
            ts=datetime.now(timezone.utc),
            collector_state=collector_state,
            sources=list(self._sources.values()),
            queue_raw_depth=self._metrics.queue_raw_depth,
            queue_canonical_depth=self._metrics.queue_canonical_depth,
            samples_total=self._metrics.samples_in,
            events_total=0,
            errors_total=self._metrics.errors,
        )

    def stop(self) -> None:
        """Idempotent no-op. CollectorApp вызывает при shutdown."""
        return
