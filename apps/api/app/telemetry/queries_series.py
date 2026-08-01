from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.edge.storage.schemas import Sample


async def fetch_samples(
    session: AsyncSession,
    tag_id: str,
    from_ts: datetime,
    to_ts: datetime,
) -> Sequence[Sample]:
    result = await session.execute(
        select(Sample)
        .where(
            and_(
                Sample.tag_id == tag_id,
                Sample.official_ts >= from_ts,
                Sample.official_ts < to_ts,
            )
        )
        .order_by(Sample.official_ts)
    )
    return result.scalars().all()


def time_bucket(bucket_seconds: int, timestamp: datetime, origin: datetime) -> datetime:
    elapsed = (timestamp - origin).total_seconds()
    bucket = int(elapsed // bucket_seconds) * bucket_seconds
    return origin + timedelta(seconds=bucket)
