"""Unit-тесты QualityEngine (s11 / CR-COL-04).

AC-B4-04 (5 quality values reachable), AC-B4-07 (out-of-range, value kept),
AC-B4-08 (NaN/Inf → bad), AC-B4-12 (YAML rules, no code change), AC-B3-06 (StatusCode → Quality).

TDD vertical slices по creative §14.3.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from collector.config.models import TagMapEntry
from collector.core.quality_engine import (
    EvalResult,
    QualityEngine,
    QualityRules,
    map_modbus_exception,
    map_opcua_status,
)
from collector.domain.models import Quality, RawSample

CANON_YAML = Path(__file__).resolve().parents[2] / "config" / "quality_rules.yaml"
NOW = datetime(2026, 7, 27, 12, 0, 0, tzinfo=timezone.utc)


# =============================================================================
# Helpers / fixtures
# =============================================================================


def _sample(
    raw_value: Any,
    native_quality: str | None = None,
    age_sec: float = 0.0,
) -> RawSample:
    return RawSample(
        source_id="aps_main",
        native_id="40101",
        raw_value=raw_value,
        native_quality=native_quality,
        recv_ts=NOW - timedelta(seconds=age_sec),
    )


def _entry(**kwargs: Any) -> TagMapEntry:
    base: dict[str, Any] = {"native_id": "40101", "tag_id": "T1", "datatype": "float32"}
    base.update(kwargs)
    return TagMapEntry(**base)


@pytest.fixture
def engine() -> QualityEngine:
    """Дефолтные QualityRules (совпадают с canon YAML)."""
    return QualityEngine(QualityRules())


@pytest.fixture
def canon_engine() -> QualityEngine:
    return QualityEngine.from_yaml(CANON_YAML)


# =============================================================================
# Slice 1 — GOOD (no native_quality, in range)
# =============================================================================


def test_good_when_no_native_quality_and_in_range(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(42.0), _entry(range_min=0, range_max=100), NOW)

    assert res.quality is Quality.GOOD
    assert res.value == 42.0
    assert res.reason is None
    assert isinstance(res, EvalResult)


# =============================================================================
# Slice 2 — NaN/Inf → BAD, value null (AC-B4-08)
# =============================================================================


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_nan_inf_returns_bad_null(engine: QualityEngine, bad: float) -> None:
    res = engine.evaluate(_sample(bad), _entry(range_min=0, range_max=100), NOW)

    assert res.quality is Quality.BAD
    assert res.value is None
    assert res.reason == "nan_inf"


# =============================================================================
# Slice 3 — out-of-range → UNCERTAIN, value kept (AC-B4-07)
# =============================================================================


def test_out_of_range_returns_uncertain_value_kept(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(150.0), _entry(range_min=0, range_max=100), NOW)

    assert res.quality is Quality.UNCERTAIN
    assert res.value == 150.0
    assert res.reason == "out_of_range"


def test_out_of_range_below_min_returns_uncertain(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(-5.0), _entry(range_min=0, range_max=100), NOW)

    assert res.quality is Quality.UNCERTAIN


def test_range_skipped_for_bool_and_str(engine: QualityEngine) -> None:
    assert engine.evaluate(_sample(True), _entry(range_min=0, range_max=100), NOW).quality is Quality.GOOD
    assert engine.evaluate(_sample("hello"), _entry(range_min=0, range_max=100), NOW).quality is Quality.GOOD


# =============================================================================
# Slice 4 — stale (per-sample age)
# =============================================================================


def test_stale_when_age_exceeds_threshold(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(42.0, age_sec=10.0), _entry(range_min=0, range_max=100), NOW)

    assert res.quality is Quality.STALE
    assert res.value == 42.0  # stale сохраняет значение
    assert res.reason == "stale"


def test_not_stale_within_threshold(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(42.0, age_sec=1.0), _entry(range_min=0, range_max=100), NOW)

    assert res.quality is Quality.GOOD


# =============================================================================
# Slice 5 — quarantine (map_entry=None) (AC-B4-04)
# =============================================================================


def test_quarantine_when_map_entry_none(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(42.0), None, NOW)

    assert res.quality is Quality.QUARANTINE
    assert res.value is None
    assert res.reason == "tag_not_in_map"


# =============================================================================
# Slice 6/7 — Modbus token mapping (typed token + YAML per-code)
# =============================================================================


def test_modbus_timeout_token_maps_to_bad(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(None, native_quality="modbus.timeout"), _entry(), NOW)

    assert res.quality is Quality.BAD
    assert res.value is None


def test_modbus_client_error_maps_to_bad(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(None, native_quality="modbus.client_error"), _entry(), NOW)

    assert res.quality is Quality.BAD


def test_modbus_exception_code_5_maps_to_uncertain(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(None, native_quality="modbus.exception.5"), _entry(), NOW)

    assert res.quality is Quality.UNCERTAIN


def test_modbus_exception_code_2_maps_to_bad(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(None, native_quality="modbus.exception.2"), _entry(), NOW)

    assert res.quality is Quality.BAD


def test_modbus_unknown_token_maps_to_bad_default(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(None, native_quality="modbus.something_new"), _entry(), NOW)

    assert res.quality is Quality.BAD  # unknown_exception default


# =============================================================================
# Slice 8/9 — OPC UA StatusCode mapping (severity-class + overrides)
# =============================================================================


def test_opcua_bad_status_maps_to_bad(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(None, native_quality="opcua.BadNoCommunication"), _entry(), NOW)

    assert res.quality is Quality.BAD


def test_opcua_uncertain_class_maps_to_uncertain(engine: QualityEngine) -> None:
    res = engine.evaluate(
        _sample(42.0, native_quality="opcua.UncertainLastUsableValue"), _entry(), NOW
    )

    assert res.quality is Quality.UNCERTAIN
    assert res.value == 42.0


def test_opcua_good_class_continues_chain(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(42.0, native_quality="opcua.Good"), _entry(range_min=0, range_max=100), NOW)

    assert res.quality is Quality.GOOD


def test_opcua_goodclamped_override_to_uncertain(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(42.0, native_quality="opcua.GoodClamped"), _entry(), NOW)

    assert res.quality is Quality.UNCERTAIN


def test_opcua_override_badwaiting_for_initial_data_to_stale(engine: QualityEngine) -> None:
    res = engine.evaluate(
        _sample(None, native_quality="opcua.BadWaitingForInitialData"), _entry(), NOW
    )

    assert res.quality is Quality.STALE


def test_opcua_unknown_status_uses_unknown_default(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(42.0, native_quality="opcua.WeirdUnknown"), _entry(), NOW)

    assert res.quality is Quality.UNCERTAIN  # unknown_status default


# =============================================================================
# Slice 10 — rule priority (fixed order)
# =============================================================================


def test_rule_priority_nan_beats_range(engine: QualityEngine) -> None:
    res = engine.evaluate(_sample(float("nan")), _entry(range_min=0, range_max=100), NOW)

    assert res.quality is Quality.BAD
    assert res.reason == "nan_inf"


def test_rule_priority_native_bad_beats_stale(engine: QualityEngine) -> None:
    res = engine.evaluate(
        _sample(None, native_quality="modbus.timeout", age_sec=10.0),
        _entry(range_min=0, range_max=100),
        NOW,
    )

    assert res.quality is Quality.BAD


def test_rule_priority_range_beats_stale(engine: QualityEngine) -> None:
    # свежий, но out-of-range → uncertain важнее stale
    res = engine.evaluate(_sample(150.0, age_sec=10.0), _entry(range_min=0, range_max=100), NOW)

    assert res.quality is Quality.UNCERTAIN
    assert res.reason == "out_of_range"


def test_native_good_does_not_short_circuit_range(engine: QualityEngine) -> None:
    res = engine.evaluate(
        _sample(150.0, native_quality="opcua.Good"), _entry(range_min=0, range_max=100), NOW
    )

    assert res.quality is Quality.UNCERTAIN


# =============================================================================
# Slice 11 — YAML reload (new instance applies edited rule, restart-only)
# =============================================================================


def test_yaml_reload_new_instance_applies_edited_rule(tmp_path: Path) -> None:
    f1 = tmp_path / "q1.yaml"
    f1.write_text("version: 1\nstale_threshold_sec: 3.0\n", encoding="utf-8")
    e1 = QualityEngine.from_yaml(f1)
    assert e1.evaluate(_sample(42.0, age_sec=10.0), _entry(range_min=0, range_max=100), NOW).quality is Quality.STALE

    f2 = tmp_path / "q2.yaml"
    f2.write_text("version: 1\nstale_threshold_sec: 1000.0\n", encoding="utf-8")
    e2 = QualityEngine.from_yaml(f2)
    assert (
        e2.evaluate(_sample(42.0, age_sec=10.0), _entry(range_min=0, range_max=100), NOW).quality is Quality.GOOD
    )


def test_canon_yaml_loads_and_applies_rules(canon_engine: QualityEngine) -> None:
    res = canon_engine.evaluate(
        _sample(None, native_quality="opcua.BadWaitingForInitialData"), _entry(), NOW
    )

    assert res.quality is Quality.STALE


# =============================================================================
# Slice 12 — value encoding (bad→null; uncertain/stale keep value)
# =============================================================================


def test_value_encoding_bad_null_uncertain_stale_keep(engine: QualityEngine) -> None:
    # bad → null
    assert engine.evaluate(_sample(float("nan")), _entry(), NOW).value is None
    # quarantine → null
    assert engine.evaluate(_sample(42.0), None, NOW).value is None
    # uncertain → keeps
    assert engine.evaluate(_sample(150.0), _entry(range_min=0, range_max=100), NOW).value == 150.0
    # stale → keeps
    assert (
        engine.evaluate(_sample(42.0, age_sec=10.0), _entry(range_min=0, range_max=100), NOW).value == 42.0
    )


# =============================================================================
# Standalone helpers (direct use / tests, not via RawSample)
# =============================================================================


def test_map_opcua_status_standalone() -> None:
    rules = QualityRules().opcua

    assert map_opcua_status("Good", rules) is Quality.GOOD
    assert map_opcua_status("BadNoCommunication", rules) is Quality.BAD
    assert map_opcua_status("UncertainLastUsableValue", rules) is Quality.UNCERTAIN
    assert map_opcua_status("GoodClamped", rules) is Quality.UNCERTAIN  # override
    assert map_opcua_status("WeirdUnknown", rules) is Quality.UNCERTAIN  # unknown default


def test_map_modbus_exception_standalone() -> None:
    rules = QualityRules().modbus

    assert map_modbus_exception("timeout", rules) is Quality.BAD
    assert map_modbus_exception("exception.5", rules) is Quality.UNCERTAIN
    assert map_modbus_exception("garbage", rules) is Quality.BAD  # unknown default
