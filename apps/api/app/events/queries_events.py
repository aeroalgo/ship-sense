from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.edge.storage.schemas import Event as DBEvent


async def fetch_events(
    session: AsyncSession,
    *,
    from_ts: datetime | None,
    to_ts: datetime | None,
    event_names: list[str] | None,
    severities: list[int] | None,
    asset_id: str | None,
    source: str | None,
    cursor: tuple[datetime, UUID] | None,
    limit: int,
) -> list[DBEvent]:
    conditions = []
    if from_ts is not None:
        conditions.append(DBEvent.official_ts >= from_ts)
    if to_ts is not None:
        conditions.append(DBEvent.official_ts <= to_ts)
    if event_names:
        conditions.append(DBEvent.event_name.in_(event_names))
    if severities:
        conditions.append(DBEvent.severity.in_(severities))
    if asset_id is not None:
        conditions.append(DBEvent.params["asset_id"].as_string() == asset_id)
    if source is not None:
        conditions.append(DBEvent.source == source)
    if cursor is not None:
        cursor_ts, cursor_id = cursor
        conditions.append(
            or_(
                DBEvent.official_ts > cursor_ts,
                and_(DBEvent.official_ts == cursor_ts, DBEvent.event_id > cursor_id),
            )
        )

    query = select(DBEvent)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(DBEvent.official_ts.asc(), DBEvent.event_id.asc()).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())
