from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.edge.storage.raid.status import RaidHealth, RaidSnapshot


@dataclass(frozen=True, slots=True)
class HealthRow:
    captured_at: datetime
    disk_total_gb: float
    disk_used_gb: float
    disk_pct: float
    ram_pct: float
    cpu_pct: float
    samples_bytes: int
    events_bytes: int
    queue_depth: int
    extra: dict[str, Any]


@dataclass(frozen=True, slots=True)
class StorageHealth:
    disk_pct: float | None
    disk_warning: bool
    raid_degraded: bool
    backup_last_ok: bool
    backup_age_hours: float | None
    overall_healthy: bool
    reason_codes: tuple[str, ...]


def reduce_storage_health(
    disk_pct: float | None,
    raid: RaidSnapshot | None,
    backup_last_ok: bool | None,
    backup_age_hours: float | None,
    *,
    backup_max_age_hours: float = 24.0,
) -> StorageHealth:
    reasons: list[str] = []
    disk_warning = disk_pct is None or disk_pct >= 80.0
    if disk_pct is None:
        reasons.append("storage.disk_unknown")
    elif disk_warning:
        reasons.append("storage.disk_high")

    raid_degraded = raid is None or raid.degraded or raid.health == RaidHealth.UNKNOWN
    if raid is None or raid.health == RaidHealth.UNKNOWN:
        reasons.append("storage.raid_unknown")
    elif raid.degraded:
        reasons.append("storage.raid_degraded")

    backup_ok = backup_last_ok is True
    if backup_last_ok is not True:
        reasons.append("storage.backup_stale")
    elif backup_age_hours is None or backup_age_hours > backup_max_age_hours:
        backup_ok = False
        reasons.append("storage.backup_stale")

    return StorageHealth(
        disk_pct=disk_pct,
        disk_warning=disk_warning,
        raid_degraded=raid_degraded,
        backup_last_ok=backup_ok,
        backup_age_hours=backup_age_hours,
        overall_healthy=not reasons,
        reason_codes=tuple(reasons),
    )


class HealthSnapshotService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        interval_seconds: float = 60.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self._session = session
        self._interval_seconds = interval_seconds
        self.logger = logger or logging.getLogger(__name__)
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def snapshot_once(
        self, queue_depth: int = 0, extra: dict[str, Any] | None = None
    ) -> HealthRow:
        disk = psutil.disk_usage("/")
        memory = psutil.virtual_memory()
        samples_result = await self._session.execute(
            text("SELECT pg_total_relation_size('samples')")
        )
        events_result = await self._session.execute(
            text("SELECT pg_total_relation_size('events')")
        )
        samples_bytes = int(samples_result.scalar_one())
        events_bytes = int(events_result.scalar_one())
        captured_at = datetime.now(timezone.utc)
        snapshot_extra = dict(extra or {})
        if disk.percent >= 80:
            snapshot_extra.setdefault("alert", "disk_80")
        row = HealthRow(
            captured_at=captured_at,
            disk_total_gb=disk.total / 1024**3,
            disk_used_gb=disk.used / 1024**3,
            disk_pct=float(disk.percent),
            ram_pct=float(memory.percent),
            cpu_pct=float(psutil.cpu_percent(interval=None)),
            samples_bytes=samples_bytes,
            events_bytes=events_bytes,
            queue_depth=queue_depth,
            extra=snapshot_extra,
        )
        await self._session.execute(
            text(
                "INSERT INTO health_snapshots "
                "(captured_at, disk_total_gb, disk_used_gb, disk_pct, ram_pct, "
                "cpu_pct, pg_size_mb, queue_depth, extra) VALUES "
                "(:captured_at, :disk_total_gb, :disk_used_gb, :disk_pct, :ram_pct, "
                ":cpu_pct, :pg_size_mb, :queue_depth, :extra)"
            ),
            {
                "captured_at": row.captured_at,
                "disk_total_gb": row.disk_total_gb,
                "disk_used_gb": row.disk_used_gb,
                "disk_pct": row.disk_pct,
                "ram_pct": row.ram_pct,
                "cpu_pct": row.cpu_pct,
                "pg_size_mb": (samples_bytes + events_bytes) / 1024**2,
                "queue_depth": row.queue_depth,
                "extra": row.extra,
            },
        )
        await self._session.commit()
        self.logger.info("storage.health.snapshot", extra={"health": row})
        return row

    async def _run(self) -> None:
        while True:
            await self.snapshot_once()
            await asyncio.sleep(self._interval_seconds)
