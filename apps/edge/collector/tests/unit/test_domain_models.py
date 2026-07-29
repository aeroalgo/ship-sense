from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from collector.domain.errors import ConfigError, ConnectError
from collector.domain.models import (
    CollectorHealthSnapshot,
    Event,
    EventSeverity,
    HealthStatus,
    Quality,
    RawSample,
    RawTagDescriptor,
    SourceState,
    TelemetrySample,
)


UTC_NOW = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)


def test_quality_has_canonical_values() -> None:
    assert [quality.value for quality in Quality] == [
        "good",
        "bad",
        "uncertain",
        "stale",
        "quarantine",
    ]


def test_raw_sample_round_trips_through_json() -> None:
    sample = RawSample(
        source_id="aps_main",
        native_id="40101",
        raw_value=42.5,
        native_quality=None,
        recv_ts=UTC_NOW,
        source_ts=UTC_NOW,
        sequence=7,
    )

    restored = RawSample.model_validate_json(sample.model_dump_json())

    assert restored == sample


def test_raw_tag_descriptor_optional_metadata_defaults_to_none() -> None:
    descriptor = RawTagDescriptor(native_id="ns=2;s=AI4101")

    assert descriptor.model_dump() == {
        "native_id": "ns=2;s=AI4101",
        "name": None,
        "unit": None,
        "datatype": None,
        "description": None,
    }


def test_telemetry_sample_serializes_quality_as_value() -> None:
    sample = TelemetrySample(
        tag_id="TAI4101",
        value=42.5,
        unit="degC",
        source_ts=UTC_NOW,
        edge_ts=UTC_NOW,
        quality=Quality.GOOD,
        source_id="aps_main",
        native_id="40101",
    )

    payload = sample.model_dump(mode="json")

    assert payload["quality"] == "good"
    assert TelemetrySample.model_validate(payload) == sample


def test_event_defaults_are_contract_values() -> None:
    event = Event(
        event_name="alarm.active",
        ts=UTC_NOW,
        edge_ts=UTC_NOW,
        source="aps_main",
        idempotency_key="key-1",
    )

    assert event.params == {}
    assert event.severity is EventSeverity.INFO
    assert event.quality is Quality.GOOD


def test_health_snapshot_round_trips_nested_source_statuses() -> None:
    source = HealthStatus(
        source_id="aps_main",
        state=SourceState.UP,
        last_ok_ts=UTC_NOW,
        reconnect_count=1,
        tags_total=586,
        tags_active=586,
        sample_rate_hz=1.0,
    )
    snapshot = CollectorHealthSnapshot(
        ts=UTC_NOW,
        collector_state="running",
        sources=[source],
        queue_raw_depth=3,
        queue_canonical_depth=1,
        samples_total=100,
        events_total=2,
        errors_total=0,
    )

    assert CollectorHealthSnapshot.model_validate_json(snapshot.model_dump_json()) == snapshot


def test_required_domain_fields_are_validated() -> None:
    with pytest.raises(ValidationError):
        RawSample(
            source_id="aps_main",
            native_id="40101",
            recv_ts=UTC_NOW,
        )


def test_domain_errors_are_exception_types() -> None:
    assert issubclass(ConnectError, Exception)
    assert issubclass(ConfigError, Exception)
