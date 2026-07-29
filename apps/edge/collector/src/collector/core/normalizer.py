from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path

from collector.config.models import TagMapEntry
from collector.core.event_detector import EventDetector
from collector.core.quality_engine import QualityEngine
from collector.core.unit_converter import UnitConverter
from collector.domain.models import Event, RawSample, TelemetrySample
from collector.util.time import utc_now

logger = logging.getLogger(__name__)


class Normalizer:
    """Convert raw source samples into canonical telemetry samples."""

    def __init__(
        self,
        *,
        tag_map: Mapping[str, TagMapEntry],
        quality_engine: QualityEngine,
        unit_converter: UnitConverter,
        event_detector: EventDetector | None = None,
        now_fn: Callable[[], datetime] = utc_now,
    ) -> None:
        self._tag_map = dict(tag_map)
        self._quality_engine = quality_engine
        self._unit_converter = unit_converter
        self._event_detector = event_detector
        self._now_fn = now_fn
        self._seen: set[tuple[str, str, datetime]] = set()
        self._events: list[Event] = []
        self._seen_event_keys: set[str] = set()

    @classmethod
    def from_yaml(
        cls,
        *,
        tag_map: Mapping[str, TagMapEntry],
        quality_rules_path: str | Path,
        units_path: str | Path,
        event_detector: EventDetector | None = None,
        now_fn: Callable[[], datetime] = utc_now,
    ) -> "Normalizer":
        return cls(
            tag_map=tag_map,
            quality_engine=QualityEngine.from_yaml(quality_rules_path),
            unit_converter=UnitConverter.from_yaml(units_path),
            event_detector=event_detector,
            now_fn=now_fn,
        )

    def __call__(
        self,
        raw: RawSample,
    ) -> tuple[TelemetrySample, list[Event]] | TelemetrySample | None:
        sample = self.process(raw)
        if sample is None:
            return None
        events = self.drain_events()
        return (sample, events) if events else sample

    def process_event(self, event: Event) -> Event | None:
        """Accept a source-native event without reconstructing it."""
        if event.idempotency_key in self._seen_event_keys:
            return None
        self._seen_event_keys.add(event.idempotency_key)
        self._events.append(event)
        return event

    def process(self, raw: RawSample) -> TelemetrySample | None:
        edge_ts = self._now_fn()
        source_ts = raw.source_ts or edge_ts
        dedup_key = (raw.native_id, source_ts)
        if dedup_key in self._seen:
            return None
        self._seen.add(dedup_key)

        map_entry = self._tag_map.get(raw.native_id)
        try:
            evaluation = self._quality_engine.evaluate(raw, map_entry, edge_ts)
            value, unit = self._unit_converter.convert(
                evaluation.value,
                map_entry.unit if map_entry is not None else None,
                map_entry.unit if map_entry is not None else None,
                map_entry.scale if map_entry is not None else None,
                map_entry.offset if map_entry is not None else None,
            )
            sample = TelemetrySample(
                tag_id=map_entry.tag_id if map_entry is not None else raw.native_id,
                value=value,
                unit=unit,
                source_ts=source_ts,
                edge_ts=edge_ts,
                quality=evaluation.quality,
                source_id=raw.source_id,
                native_id=raw.native_id,
            )
        except Exception:
            logger.exception(
                "Failed to normalize raw sample: source=%s native_id=%s",
                raw.source_id,
                raw.native_id,
            )
            return None

        if self._event_detector is not None and not _skip_event_detector(map_entry):
            event = self._event_detector.detect(
                tag_id=sample.tag_id,
                value=sample.value,
                ts=sample.source_ts,
                edge_ts=sample.edge_ts,
                source=sample.source_id,
                quality=sample.quality,
                discrete=map_entry is not None and _is_discrete(map_entry),
            )
            if event is not None:
                self._events.append(event)
        return sample

    def drain_events(self) -> list[Event]:
        events, self._events = self._events, []
        return events


def _skip_event_detector(entry: TagMapEntry | None) -> bool:
    return entry is not None and (
        entry.model_dump().get("skip_event_detector") is True
        or entry.model_dump().get("source") == "mqtt"
    )


def _is_discrete(entry: TagMapEntry) -> bool:
    datatype = entry.datatype.lower()
    return datatype in {
        "bool",
        "boolean",
        "bit",
        "discrete",
        "enum",
        "int",
        "integer",
    }
