from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.edge.collector.src.collector.domain.models import Quality, TelemetrySample
from apps.edge.storage.schemas import Sample


@dataclass(frozen=True, slots=True)
class SamplePoint:
    tag_id: str
    ts: datetime
    value: float | None
    quality: int
    official_ts: datetime


_QUALITY_CODE = {
    Quality.GOOD: 0,
    Quality.UNCERTAIN: 1,
    Quality.BAD: 2,
    Quality.STALE: 3,
    Quality.QUARANTINE: 4,
}


class SamplesRepo:
    def __init__(self, session: AsyncSession, *, copy_threshold: int = 1000) -> None:
        self._session = session
        self._copy_threshold = copy_threshold

    async def insert_batch(self, samples: list[TelemetrySample]) -> int:
        rows: dict[tuple[str, datetime], dict[str, Any]] = {}
        for sample in samples:
            ts = sample.source_ts
            quality = _QUALITY_CODE[sample.quality]
            key = (sample.tag_id, ts)
            row = {
                "tag_id": sample.tag_id,
                "ts": ts,
                "value": _numeric_value(sample.value),
                "quality": quality,
                "source_ts": sample.source_ts,
                "edge_ts": sample.edge_ts,
                "official_ts": ts,
            }
            previous = rows.get(key)
            if previous is None or quality <= previous["quality"]:
                rows[key] = row

        if not rows:
            return 0

        statement = insert(Sample).values(list(rows.values()))
        excluded = statement.excluded
        statement = statement.on_conflict_do_update(
            index_elements=[Sample.tag_id, Sample.ts],
            set_={
                "value": excluded.value,
                "quality": Sample.quality,
                "source_ts": excluded.source_ts,
                "edge_ts": excluded.edge_ts,
                "official_ts": excluded.official_ts,
            },
            where=excluded.quality <= Sample.quality,
        )
        await self._session.execute(statement)
        await self._session.commit()
        return len(rows)

    async def query_trend(
        self,
        tag_id: str,
        t0: datetime,
        t1: datetime,
        max_points: int = 1000,
    ) -> list[SamplePoint]:
        if max_points <= 0:
            return []
        result = await self._session.execute(
            select(Sample)
            .where(and_(Sample.tag_id == tag_id, Sample.ts >= t0, Sample.ts < t1))
            .order_by(Sample.ts)
            .limit(max_points)
        )
        return [_to_point(row) for row in result.scalars()]

    async def query_point(self, tag_id: str, ts: datetime) -> SamplePoint | None:
        result = await self._session.execute(
            select(Sample).where(Sample.tag_id == tag_id, Sample.ts == ts)
        )
        row = result.scalar_one_or_none()
        return None if row is None else _to_point(row)


def _numeric_value(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError("samples.value must be numeric or None")


def _to_point(row: Sample) -> SamplePoint:
    return SamplePoint(
        tag_id=row.tag_id,
        ts=row.ts,
        value=row.value,
        quality=row.quality,
        official_ts=row.official_ts,
    )
