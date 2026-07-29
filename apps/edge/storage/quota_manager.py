from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class DiskUsage:
    total_bytes: int
    used_bytes: int
    postgres_bytes: int

    @property
    def percent(self) -> float:
        return self.used_bytes / self.total_bytes * 100 if self.total_bytes else 0.0


@dataclass(frozen=True, slots=True)
class QuotaSettings:
    alert_pct: float = 80.0
    samples_quota_bytes: int = 0


@dataclass(frozen=True, slots=True)
class DegradeResult:
    alerted: bool
    degraded_chunks: int
    bytes_freed: int


class QuotaManager:
    def __init__(self, session: AsyncSession, *, settings: QuotaSettings | None = None) -> None:
        self._session = session
        self._settings = settings or QuotaSettings()

    async def get_current_usage(self) -> DiskUsage:
        usage = psutil.disk_usage("/")
        result = await self._session.execute(text("SELECT pg_database_size(current_database())"))
        postgres_bytes = int(result.scalar_one())
        return DiskUsage(usage.total, usage.used + postgres_bytes, postgres_bytes)

    async def check_and_degrade(self) -> DegradeResult:
        usage = await self._disk_usage()
        alerted = usage.percent >= self._settings.alert_pct
        if alerted:
            await self._session.execute(
                text("INSERT INTO health_snapshots (captured_at, extra) VALUES (:captured_at, :extra)"),
                {"captured_at": datetime.now(timezone.utc), "extra": {"alert": "disk_80"}},
            )

        samples_bytes = await self._samples_size()
        if samples_bytes <= self._settings.samples_quota_bytes:
            return DegradeResult(alerted, 0, 0)

        chunks = await self._oldest_chunks()
        remaining = samples_bytes - self._settings.samples_quota_bytes
        dropped = 0
        freed = 0
        for chunk_name, chunk_bytes in chunks:
            await self._drop_chunk(chunk_name)
            await self._session.execute(
                text("INSERT INTO samples_degrade_log (chunk_name, bytes_freed) VALUES (:chunk_name, :bytes_freed)"),
                {"chunk_name": chunk_name, "bytes_freed": chunk_bytes},
            )
            dropped += 1
            freed += int(chunk_bytes)
            remaining -= int(chunk_bytes)
            if remaining <= 0:
                break

        await self._session.execute(
            text("UPDATE samples_degrade_watermark SET watermark = :watermark WHERE id = 1"),
            {"watermark": datetime.now(timezone.utc)},
        )
        return DegradeResult(alerted, dropped, freed)

    async def _disk_usage(self) -> DiskUsage:
        return await self.get_current_usage()

    async def _samples_size(self) -> int:
        result = await self._session.execute(
            text("SELECT pg_total_relation_size('samples')")
        )
        return int(result.scalar_one())

    async def _oldest_chunks(self) -> list[tuple[str, int]]:
        result = await self._session.execute(
            text(
                "SELECT chunk_name, total_bytes "
                "FROM timescaledb_information.chunks "
                "WHERE hypertable_name = 'samples' "
                "ORDER BY is_compressed ASC, range_start ASC"
            )
        )
        return [(str(name), int(size)) for name, size in result.all()]

    async def _drop_chunk(self, chunk_name: str) -> None:
        await self._session.execute(
            text("SELECT drop_chunks(:chunk_name, 'samples')"),
            {"chunk_name": chunk_name},
        )
