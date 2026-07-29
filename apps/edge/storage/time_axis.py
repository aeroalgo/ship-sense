from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from apps.edge.storage.schemas import Event as DBEvent, ClockShiftLog as DBClockShiftLog


class OfficialDateTime(datetime):
    quality: str

    def __new__(
        cls,
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        microsecond: int = 0,
        tzinfo: Any = None,
        *,
        fold: int = 0,
        quality: str = "good"
    ) -> "OfficialDateTime":
        self = datetime.__new__(
            cls, year, month, day, hour, minute, second, microsecond, tzinfo, fold=fold
        )
        object.__setattr__(self, "quality", quality)
        return self

    @classmethod
    def from_datetime(cls, dt: datetime, quality: str = "good") -> "OfficialDateTime":
        return cls(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            dt.tzinfo,
            fold=dt.fold,
            quality=quality,
        )


@dataclass(frozen=True)
class ClockShift:
    detected_on: str
    delta: timedelta
    prev_ts: datetime
    new_ts: datetime


class TimeAxisService:
    def __init__(
        self,
        prefer_source_ts: bool = True,
        max_skew_sec: float = 86400.0,
        backward_jump_sec: float = 60.0,
        forward_jump_sec: float = 300.0,
    ) -> None:
        self.prefer_source_ts = prefer_source_ts
        self.max_skew_sec = max_skew_sec
        self.backward_jump_sec = backward_jump_sec
        self.forward_jump_sec = forward_jump_sec

    def compute_official_ts(
        self, source_ts: datetime, edge_ts: datetime, source_time_quality: str
    ) -> OfficialDateTime:
        if not self.prefer_source_ts:
            return OfficialDateTime.from_datetime(edge_ts, quality="good")

        if source_ts.year < 2000 or source_ts.year > 2100:
            return OfficialDateTime.from_datetime(edge_ts, quality="time_bad")

        skew = abs((source_ts - edge_ts).total_seconds())
        if skew > self.max_skew_sec:
            return OfficialDateTime.from_datetime(edge_ts, quality="time_bad")

        if source_time_quality != "good":
            return OfficialDateTime.from_datetime(edge_ts, quality="time_bad")

        return OfficialDateTime.from_datetime(source_ts, quality="good")

    def detect_clock_shift(self, prev_edge: datetime, new_edge: datetime) -> ClockShift | None:
        delta = new_edge - prev_edge
        delta_sec = delta.total_seconds()
        if delta_sec < -self.backward_jump_sec:
            return ClockShift(
                detected_on="edge",
                delta=delta,
                prev_ts=prev_edge,
                new_ts=new_edge,
            )
        elif delta_sec > self.forward_jump_sec:
            return ClockShift(
                detected_on="edge",
                delta=delta,
                prev_ts=prev_edge,
                new_ts=new_edge,
            )
        return None

    async def record_clock_shift(self, shift: ClockShift, events_repo: Any) -> None:
        prev_dt = shift.prev_ts if shift.prev_ts.tzinfo is not None else shift.prev_ts.replace(tzinfo=timezone.utc)
        new_dt = shift.new_ts if shift.new_ts.tzinfo is not None else shift.new_ts.replace(tzinfo=timezone.utc)
        prev_ts_int = int(prev_dt.astimezone(timezone.utc).timestamp())
        new_ts_int = int(new_dt.astimezone(timezone.utc).timestamp())

        idempotency_key = f"clock_shift_{shift.detected_on}_{prev_ts_int}_{new_ts_int}"

        # Проверяем существующий event
        stmt_sel = select(DBEvent.event_id).where(DBEvent.idempotency_key == idempotency_key)
        res_sel = await events_repo._session.execute(stmt_sel)
        existing_event_id = res_sel.scalar_one_or_none()

        if existing_event_id is None:
            event_id = uuid.uuid4()
            stmt = (
                insert(DBEvent)
                .values(
                    event_id=event_id,
                    idempotency_key=idempotency_key,
                    event_name="clock_shift",
                    source=shift.detected_on,
                    source_ts=shift.new_ts,
                    edge_ts=shift.new_ts,
                    official_ts=shift.new_ts,
                    params={
                        "prev_ts": shift.prev_ts.isoformat(),
                        "new_ts": shift.new_ts.isoformat(),
                        "delta_seconds": shift.delta.total_seconds(),
                    },
                    severity=1,
                    reconstructed=False,
                )
                .on_conflict_do_nothing(index_elements=["idempotency_key"])
            )

            res = await events_repo._session.execute(stmt)
            if res.rowcount > 0:
                log_stmt = insert(DBClockShiftLog).values(
                    detected_on=shift.detected_on,
                    delta=shift.delta,
                    prev_ts=shift.prev_ts,
                    new_ts=shift.new_ts,
                    linked_event_id=event_id,
                )
                await events_repo._session.execute(log_stmt)
                await events_repo._session.commit()
