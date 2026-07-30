from __future__ import annotations

from datetime import datetime, timezone

from collector.config.models import TagMapEntry
from collector.core.event_detector import EventDetector
from collector.core.normalizer import Normalizer
from collector.core.quality_engine import QualityEngine
from collector.core.unit_converter import UnitConverter, UnitRules
from app.events.models import Event
from collector.domain.raw_models import RawSample

EDGE_NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


def _raw(*, native_id: str, value: object, source_id: str, source_ts: datetime) -> RawSample:
    return RawSample(
        source_id=source_id,
        native_id=native_id,
        raw_value=value,
        recv_ts=EDGE_NOW,
        source_ts=source_ts,
    )


def _entry(*, native_id: str, tag_id: str, source: str | None = None) -> TagMapEntry:
    values: dict[str, object] = {
        "native_id": native_id,
        "tag_id": tag_id,
        "datatype": "bool",
        "unit": None,
    }
    if source is not None:
        values["source"] = source
    return TagMapEntry.model_validate(values)


def _normalizer(entries: dict[str, TagMapEntry]) -> Normalizer:
    return Normalizer(
        tag_map=entries,
        quality_engine=QualityEngine.from_yaml(
            "apps/edge/collector/config/quality_rules.yaml"
        ),
        unit_converter=UnitConverter(UnitRules()),
        event_detector=EventDetector(),
        now_fn=lambda: EDGE_NOW,
    )


def test_mqtt_tag_skips_event_detector_reconstruction() -> None:
    normalizer = _normalizer(
        {
            "mqtt.di": _entry(native_id="mqtt.di", tag_id="DI-MQTT", source="mqtt"),
            "modbus.di": _entry(native_id="modbus.di", tag_id="DI-MODBUS"),
        }
    )
    first_ts = EDGE_NOW
    second_ts = EDGE_NOW.replace(second=1)

    assert normalizer.process(
        _raw(native_id="mqtt.di", value=False, source_id="panel_aps", source_ts=first_ts)
    ) is not None
    assert normalizer.process(
        _raw(native_id="mqtt.di", value=True, source_id="panel_aps", source_ts=second_ts)
    ) is not None
    assert normalizer.drain_events() == []

    assert normalizer.process(
        _raw(native_id="modbus.di", value=False, source_id="modbus", source_ts=first_ts)
    ) is not None
    assert normalizer.process(
        _raw(native_id="modbus.di", value=True, source_id="modbus", source_ts=second_ts)
    ) is not None
    events = normalizer.drain_events()
    assert len(events) == 1
    assert events[0].tag_id == "DI-MODBUS"


def test_mqtt_event_passes_through_and_deduplicates_by_idempotency_key() -> None:
    normalizer = _normalizer({})
    event = Event(
        event_name="aps.threshold.exceeded",
        params={"lifecycle": "exceeded", "reconstructed": False},
        ts=EDGE_NOW,
        edge_ts=EDGE_NOW,
        source="panel_aps",
        tag_id="TAI4101",
        idempotency_key="panel_aps:TAI4101:exceeded:2026-07-28T12:00:00+00:00",
    )

    assert normalizer.process_event(event) is event
    assert normalizer.process_event(event) is None
    assert normalizer.drain_events() == [event]
