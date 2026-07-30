from __future__ import annotations

from datetime import datetime, timezone

from collector.config.models import TagMapEntry
from collector.core.event_detector import EventDetector
from collector.core.normalizer import Normalizer
from collector.core.quality_engine import QualityEngine
from collector.core.unit_converter import UnitConverter, UnitRules
from app.events.models import Event
from app.telemetry.models import Quality
from collector.domain.raw_models import RawSample
from collector.util.time import utc_now


EDGE_NOW = datetime(2026, 7, 27, 12, 0, tzinfo=timezone.utc)


def _raw(
    *,
    native_id: str = "40101",
    value: object = 10,
    source_id: str = "aps_main",
    source_ts: datetime | None = EDGE_NOW,
    native_quality: str | None = None,
) -> RawSample:
    return RawSample(
        source_id=source_id,
        native_id=native_id,
        raw_value=value,
        native_quality=native_quality,
        recv_ts=EDGE_NOW,
        source_ts=source_ts,
    )


def _entry(
    *,
    native_id: str = "40101",
    tag_id: str = "TAI4101",
    unit: str | None = "K",
    datatype: str = "float",
    scale: float | None = None,
    offset: float | None = None,
) -> TagMapEntry:
    return TagMapEntry(
        native_id=native_id,
        tag_id=tag_id,
        datatype=datatype,
        unit=unit,
        scale=scale,
        offset=offset,
    )


def _normalizer(entries: dict[str, TagMapEntry] | None = None) -> Normalizer:
    return Normalizer(
        tag_map=entries or {"40101": _entry()},
        quality_engine=QualityEngine.from_yaml(
            "apps/edge/collector/config/quality_rules.yaml"
        ),
        unit_converter=UnitConverter(UnitRules()),
        now_fn=lambda: EDGE_NOW,
    )


def test_raw_is_mapped_and_timestamp_fallback_uses_edge_now() -> None:
    normalizer = _normalizer({"40101": _entry(unit="degC")})

    result = normalizer.process(_raw(value=21, source_ts=None))

    assert result is not None
    assert result.tag_id == "TAI4101"
    assert result.value == 21
    assert result.unit == "degC"
    assert result.edge_ts == EDGE_NOW
    assert result.source_ts == EDGE_NOW
    assert result.quality is Quality.GOOD


def test_unit_conversion_and_per_tag_calibration_are_wired() -> None:
    normalizer = _normalizer(
        {"40101": _entry(unit="K", scale=2.0, offset=1.0)}
    )

    result = normalizer.process(_raw(value=10))

    assert result is not None
    assert result.value == 21.0
    assert result.unit == "K"


def test_missing_tag_is_quarantined_without_crashing() -> None:
    result = _normalizer({}).process(_raw(native_id="99999", value=1))

    assert result is not None
    assert result.tag_id == "99999"
    assert result.value is None
    assert result.unit == "unknown"
    assert result.quality is Quality.QUARANTINE


def test_duplicate_native_id_and_source_timestamp_is_ignored() -> None:
    normalizer = _normalizer()
    raw = _raw(value=10)

    assert normalizer.process(raw) is not None
    assert normalizer.process(raw) is None


def test_duplicate_native_id_and_source_timestamp_across_sources_is_ignored() -> None:
    normalizer = _normalizer()
    first = _raw(value=10, source_id="modbus")
    duplicate = _raw(value=10, source_id="opcua")

    assert normalizer.process(first) is not None
    assert normalizer.process(duplicate) is None


def test_discrete_change_emits_one_event_as_side_effect() -> None:
    normalizer = Normalizer(
        tag_map={
            "00001": _entry(
                native_id="00001",
                tag_id="DI0001",
                unit=None,
                datatype="bool",
            )
        },
        quality_engine=QualityEngine.from_yaml(
            "apps/edge/collector/config/quality_rules.yaml"
        ),
        unit_converter=UnitConverter(UnitRules()),
        event_detector=EventDetector(),
        now_fn=lambda: EDGE_NOW,
    )

    assert normalizer.process(_raw(native_id="00001", value=False)) is not None
    assert normalizer.drain_events() == []
    sample = normalizer.process(
        _raw(
            native_id="00001",
            value=True,
            source_ts=EDGE_NOW.replace(second=1),
        )
    )
    events = normalizer.drain_events()

    assert sample is not None
    assert len(events) == 1
    assert isinstance(events[0], Event)
    assert events[0].event_name == "discrete.changed"
    assert events[0].tag_id == "DI0001"
    assert events[0].params == {"from": False, "to": True}


def test_bad_native_quality_does_not_raise_and_encodes_null() -> None:
    result = _normalizer().process(
        _raw(value=10, native_quality="modbus.timeout")
    )

    assert result is not None
    assert result.quality is Quality.BAD
    assert result.value is None


def test_utc_now_is_aware() -> None:
    now = utc_now()

    assert now.tzinfo is not None
    assert now.utcoffset() is not None
