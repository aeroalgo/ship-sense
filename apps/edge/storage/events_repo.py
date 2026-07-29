from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.edge.collector.src.collector.domain.models import Event as DomainEvent, EventSeverity
from apps.edge.storage.schemas import Event as DBEvent, Sample as DBSample
from apps.edge.storage.samples_repo import SamplePoint


@dataclass(frozen=True)
class EventFilters:
    ts_from: datetime | None = None
    ts_to: datetime | None = None
    event_name: str | None = None
    source: str | None = None
    tag_id: str | None = None
    lifecycle: str | None = None
    ack_state: str | None = None


@dataclass(frozen=True)
class EventRow:
    event_id: UUID
    idempotency_key: str
    event_name: str
    source: str
    source_ts: datetime
    edge_ts: datetime
    official_ts: datetime
    params: dict[str, Any]
    severity: int | None
    reconstructed: bool
    ingested_at: datetime


@dataclass(frozen=True)
class EventWithSample:
    event: EventRow
    sample: SamplePoint | None


_SEVERITY_CODE = {
    "info": 0,
    "warning": 1,
    "alarm": 2,
    "protection": 3,
    EventSeverity.INFO: 0,
    EventSeverity.WARNING: 1,
    EventSeverity.ALARM: 2,
    EventSeverity.PROTECTION: 3,
}


def _to_event_row(row: DBEvent) -> EventRow:
    return EventRow(
        event_id=row.event_id,
        idempotency_key=row.idempotency_key,
        event_name=row.event_name,
        source=row.source,
        source_ts=row.source_ts,
        edge_ts=row.edge_ts,
        official_ts=row.official_ts,
        params=row.params,
        severity=row.severity,
        reconstructed=row.reconstructed,
        ingested_at=row.ingested_at,
    )


def _to_sample_point(row: DBSample) -> SamplePoint:
    return SamplePoint(
        tag_id=row.tag_id,
        ts=row.ts,
        value=row.value,
        quality=row.quality,
        official_ts=row.official_ts,
    )


class EventsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_batch(self, events: list[DomainEvent]) -> int:
        rows = {}
        for event in events:
            reconstructed = bool(
                event.params.get("reconstructed")
                or event.params.get("mode") == "reconstruct"
            )
            params = dict(event.params)
            if event.tag_id is not None:
                params["tag_id"] = event.tag_id
            if event.quality is not None:
                params["quality"] = str(event.quality.value)

            severity_val = _SEVERITY_CODE.get(event.severity) if event.severity is not None else None

            row = {
                "idempotency_key": event.idempotency_key,
                "event_name": event.event_name,
                "source": event.source,
                "source_ts": event.ts,
                "edge_ts": event.edge_ts,
                "official_ts": event.ts,
                "params": params,
                "severity": severity_val,
                "reconstructed": reconstructed,
            }
            rows[event.idempotency_key] = row

        if not rows:
            return 0

        statement = insert(DBEvent).values(list(rows.values()))
        statement = statement.on_conflict_do_nothing(
            index_elements=["idempotency_key"]
        )
        res = await self._session.execute(statement)
        await self._session.commit()
        return res.rowcount

    async def query_journal(self, filters: EventFilters, limit: int, offset: int = 0) -> list[EventRow]:
        query = select(DBEvent)
        conditions = []
        if filters.ts_from is not None:
            conditions.append(DBEvent.official_ts >= filters.ts_from)
        if filters.ts_to is not None:
            conditions.append(DBEvent.official_ts <= filters.ts_to)
        if filters.event_name is not None:
            conditions.append(DBEvent.event_name == filters.event_name)
        if filters.source is not None:
            conditions.append(DBEvent.source == filters.source)
        if filters.tag_id is not None:
            conditions.append(DBEvent.params["tag_id"].as_string() == filters.tag_id)
        if filters.lifecycle is not None:
            conditions.append(DBEvent.params["lifecycle"].as_string() == filters.lifecycle)
        if filters.ack_state is not None:
            conditions.append(DBEvent.params["ack_state"].as_string() == filters.ack_state)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(DBEvent.official_ts.desc(), DBEvent.event_id.desc()).limit(limit).offset(offset)
        res = await self._session.execute(query)
        db_events = res.scalars().all()
        return [_to_event_row(e) for e in db_events]

    async def get_with_sample(self, event_id: UUID, window_ms: int = 0) -> EventWithSample:
        event_res = await self._session.execute(select(DBEvent).where(DBEvent.event_id == event_id))
        event = event_res.scalar_one_or_none()
        if event is None:
            raise ValueError(f"Event with id {event_id} not found")

        tag_id = event.params.get("tag_id")
        if not tag_id:
            return EventWithSample(event=_to_event_row(event), sample=None)

        window = timedelta(milliseconds=window_ms)

        stmt1 = (
            select(DBSample)
            .where(
                DBSample.tag_id == tag_id,
                DBSample.official_ts <= event.official_ts,
                DBSample.official_ts >= event.official_ts - window
            )
            .order_by(DBSample.official_ts.desc())
            .limit(1)
        )
        res1 = await self._session.execute(stmt1)
        sample1 = res1.scalar_one_or_none()

        stmt2 = (
            select(DBSample)
            .where(
                DBSample.tag_id == tag_id,
                DBSample.official_ts >= event.official_ts,
                DBSample.official_ts <= event.official_ts + window
            )
            .order_by(DBSample.official_ts.asc())
            .limit(1)
        )
        res2 = await self._session.execute(stmt2)
        sample2 = res2.scalar_one_or_none()

        best_sample = None
        if sample1 and sample2:
            diff1 = abs((sample1.official_ts - event.official_ts).total_seconds())
            diff2 = abs((sample2.official_ts - event.official_ts).total_seconds())
            best_sample = sample1 if diff1 <= diff2 else sample2
        elif sample1:
            best_sample = sample1
        elif sample2:
            best_sample = sample2

        sample_point = _to_sample_point(best_sample) if best_sample else None
        return EventWithSample(event=_to_event_row(event), sample=sample_point)
