"""Telemetry services used by read-only API endpoints."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Protocol

from app.semantic.engine import SemanticEngine
from app.semantic.models import SignalType
from app.telemetry.models import Quality
from app.telemetry.queries_series import fetch_samples
from app.telemetry.schemas import (
    AggregateFunction,
    AggregateSeries,
    Resolution,
    SeriesAggregateResponse,
    SeriesPoint,
    SeriesResponse,
)


@dataclass(frozen=True, slots=True)
class LatestValue:
    value: float | int | bool | None
    quality: str
    timestamp: datetime | None = None


class LatestValueCache:
    def __init__(self) -> None:
        self._values: dict[str, LatestValue] = {}
        self._lock = Lock()

    def set(
        self,
        tag_id: str,
        value: float | int | bool | None,
        *,
        quality: str = "good",
        timestamp: datetime | None = None,
    ) -> None:
        with self._lock:
            self._values[tag_id] = LatestValue(value, quality, timestamp)

    def get(self, tag_id: str) -> LatestValue | None:
        with self._lock:
            return self._values.get(tag_id)


_latest_value_cache = LatestValueCache()


def get_latest_value_cache() -> LatestValueCache:
    return _latest_value_cache


_NICE_BUCKETS: tuple[tuple[int, str], ...] = (
    (1, "1s"),
    (2, "2s"),
    (5, "5s"),
    (10, "10s"),
    (30, "30s"),
    (60, "1m"),
    (300, "5m"),
    (600, "10m"),
    (900, "15m"),
    (3_600, "1h"),
    (14_400, "4h"),
    (86_400, "1d"),
)
_BUCKET_SECONDS = {label: seconds for seconds, label in _NICE_BUCKETS}
_BUCKET_SECONDS["raw"] = 0


def pick_resolution(
    from_ts: datetime,
    to_ts: datetime,
    target: int = 1_500,
) -> Resolution:
    """Choose the smallest nice bucket that keeps the response near target points."""
    if target <= 0:
        raise ValueError("target must be positive")
    span_sec = (to_ts - from_ts).total_seconds()
    if span_sec <= 0:
        raise ValueError("to must be greater than from")
    if span_sec <= target:
        return "raw"
    bucket_sec = math.ceil(span_sec / target)
    for seconds, label in _NICE_BUCKETS:
        if seconds >= bucket_sec:
            return label  # type: ignore[return-value]
    return "1d"


class SampleLike(Protocol):
    official_ts: datetime
    value: float | None
    quality: int


_QUALITY_BY_CODE = {
    0: Quality.GOOD,
    1: Quality.UNCERTAIN,
    2: Quality.BAD,
    3: Quality.STALE,
    4: Quality.QUARANTINE,
    5: Quality.QUARANTINE,
}


class DownsampleService:
    def __init__(self, session: object, engine: SemanticEngine) -> None:
        self._session = session
        self._engine = engine

    async def fetch_series(
        self,
        tag_id: str,
        from_ts: datetime,
        to_ts: datetime,
        resolution: str = "auto",
    ) -> SeriesResponse:
        meta = self._tag_meta(tag_id)
        selected = self._resolution(from_ts, to_ts, resolution)
        rows = await fetch_samples(self._session, tag_id, from_ts, to_ts)
        points = _downsample(rows, from_ts, selected, meta.signal_type)
        return SeriesResponse(
            tag_id=tag_id,
            name=meta.label or tag_id,
            unit=meta.unit,
            **{"from": from_ts},
            to=to_ts,
            resolution=selected,
            points=points,
        )

    async def fetch_aggregate(
        self,
        tags: list[str],
        from_ts: datetime,
        to_ts: datetime,
        resolution: str = "auto",
        fn: AggregateFunction = "avg",
    ) -> SeriesAggregateResponse:
        if not tags:
            raise ValueError("tags must not be empty")
        selected = self._resolution(from_ts, to_ts, resolution)
        series: list[AggregateSeries] = []
        for tag_id in tags:
            meta = self._tag_meta(tag_id)
            rows = await fetch_samples(self._session, tag_id, from_ts, to_ts)
            points = _downsample(rows, from_ts, selected, meta.signal_type, fn=fn)
            series.append(AggregateSeries(tag_id=tag_id, unit=meta.unit, points=points))
        return SeriesAggregateResponse(
            **{"from": from_ts}, to=to_ts, resolution=selected, series=series
        )

    def _tag_meta(self, tag_id: str):
        try:
            return self._engine.get_tag_meta(tag_id)
        except KeyError as exc:
            raise LookupError(tag_id) from exc

    @staticmethod
    def _resolution(from_ts: datetime, to_ts: datetime, value: str) -> Resolution:
        if value == "auto":
            return pick_resolution(from_ts, to_ts)
        if value not in _BUCKET_SECONDS:
            raise ValueError("unsupported resolution")
        if to_ts <= from_ts:
            raise ValueError("to must be greater than from")
        return value  # type: ignore[return-value]


def _downsample(
    rows: list[SampleLike] | tuple[SampleLike, ...],
    origin: datetime,
    resolution: Resolution,
    signal_type: SignalType,
    *,
    fn: AggregateFunction = "avg",
) -> list[SeriesPoint]:
    bucket_seconds = _BUCKET_SECONDS[resolution]
    if resolution == "raw":
        return [
            SeriesPoint(
                ts=row.official_ts,
                value=row.value,
                quality=_quality(row.quality),
                min=row.value,
                max=row.value,
                samples=1,
            )
            for row in rows
        ]

    buckets: dict[datetime, list[SampleLike]] = {}
    for row in rows:
        elapsed = (row.official_ts - origin).total_seconds()
        bucket = origin + timedelta(seconds=int(elapsed // bucket_seconds) * bucket_seconds)
        buckets.setdefault(bucket, []).append(row)

    points: list[SeriesPoint] = []
    for timestamp, bucket_rows in buckets.items():
        values = [row.value for row in bucket_rows if row.value is not None]
        numeric = [float(value) for value in values if not isinstance(value, bool)]
        if signal_type in (SignalType.DIGITAL, SignalType.ALARM_BIT):
            value = values[-1] if values else None
        elif fn == "min":
            value = min(numeric) if numeric else None
        elif fn == "max":
            value = max(numeric) if numeric else None
        elif fn == "last":
            value = values[-1] if values else None
        else:
            value = sum(numeric) / len(numeric) if numeric else None
        points.append(
            SeriesPoint(
                ts=timestamp,
                value=value,
                quality=max((_quality(row.quality) for row in bucket_rows), key=_quality_rank),
                min=min(numeric) if numeric else None,
                max=max(numeric) if numeric else None,
                samples=len(bucket_rows),
            )
        )
    return points


def _quality(value: int) -> Quality:
    return _QUALITY_BY_CODE.get(value, Quality.QUARANTINE)


def _quality_rank(value: Quality) -> int:
    return {
        Quality.GOOD: 1,
        Quality.UNCERTAIN: 2,
        Quality.BAD: 3,
        Quality.STALE: 4,
        Quality.QUARANTINE: 5,
    }[value]
