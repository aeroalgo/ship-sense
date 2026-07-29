"""Unit-тесты UnitConverter (s12).

AC-B4-03 (unit conversion через справочник + scale/offset из карты),
AC-B4-09 (unknown unit → unit=unknown + warning log).

TDD vertical slices по plan §14.3.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from collector.config.models import TagMapEntry
from collector.core.unit_converter import (
    ConversionRule,
    UnitConverter,
    UnitRules,
)

CANON_YAML = Path(__file__).resolve().parents[2] / "config" / "units.yaml"


# =============================================================================
# Helpers
# =============================================================================


def _rules(**overrides: Any) -> UnitRules:
    """Конвертер с минимумом правил для тестов."""
    base = UnitRules(
        aliases={"°C": "degC", "deg C": "degC", "C": "degC", "k": "K"},
        conversions=[
            ConversionRule(from_="degC", to="K", scale=1.0, offset=273.15),
            ConversionRule(from_="K", to="degC", scale=1.0, offset=-273.15),
            ConversionRule(from_="bar", to="kPa", scale=100.0, offset=0.0),
            ConversionRule(from_="kPa", to="bar", scale=0.01, offset=0.0),
        ],
    )
    return base.model_copy(overrides) if overrides else base


@pytest.fixture
def conv() -> UnitConverter:
    return UnitConverter(_rules())


# =============================================================================
# AC-B4-03 — unit conversion через справочник
# =============================================================================


def test_identity_same_unit_no_change(conv: UnitConverter) -> None:
    value, unit = conv.convert(20.0, "degC", "degC")
    assert value == 20.0
    assert unit == "degC"


def test_alias_resolved_to_canonical_identity(conv: UnitConverter) -> None:
    """Алиас °C и канон degC — одна величина, identity после resolve."""
    value, unit = conv.convert(20.0, "°C", "degC")
    assert value == 20.0
    assert unit == "degC"


def test_conversion_degC_to_K(conv: UnitConverter) -> None:
    value, unit = conv.convert(0.0, "degC", "K")
    assert value == pytest.approx(273.15)
    assert unit == "K"


def test_conversion_K_to_degC(conv: UnitConverter) -> None:
    value, unit = conv.convert(273.15, "K", "degC")
    assert value == pytest.approx(0.0, abs=1e-9)
    assert unit == "degC"


def test_conversion_bar_to_kPa(conv: UnitConverter) -> None:
    value, unit = conv.convert(1.0, "bar", "kPa")
    assert value == pytest.approx(100.0)
    assert unit == "kPa"


def test_conversion_kPa_to_bar(conv: UnitConverter) -> None:
    value, unit = conv.convert(100.0, "kPa", "bar")
    assert value == pytest.approx(1.0)
    assert unit == "bar"


def test_alias_source_applies_conversion(conv: UnitConverter) -> None:
    """Алиас на стороне from резолвится, затем применяется conversion."""
    value, unit = conv.convert(100.0, "C", "K")  # C → degC → K
    assert value == pytest.approx(373.15)
    assert unit == "K"


# =============================================================================
# Per-tag scale/offset из карты (plan §14.3 per-tag override)
# =============================================================================


def test_per_tag_scale_offset_calibration(conv: UnitConverter) -> None:
    """Raw register 0..32000 → 0..32 bar через scale=0.001 из TagMapEntry."""
    entry = TagMapEntry(
        native_id="HR1", tag_id="PAI3001", datatype="float32",
        scale=0.001, offset=0.0, unit="bar",
    )
    value, unit = conv.convert(32000, "raw", entry.unit, entry.scale, entry.offset)
    assert value == pytest.approx(32.0)
    assert unit == "bar"


def test_per_tag_offset_applied(conv: UnitConverter) -> None:
    entry = TagMapEntry(
        native_id="HR1", tag_id="PAI3002", datatype="float32",
        scale=2.0, offset=10.0, unit="bar",
    )
    value, unit = conv.convert(5.0, "raw", entry.unit, entry.scale, entry.offset)
    assert value == pytest.approx(20.0)  # 5*2 + 10
    assert unit == "bar"


def test_per_tag_scale_only_offset_defaults_zero(conv: UnitConverter) -> None:
    entry = TagMapEntry(
        native_id="HR1", tag_id="PAI3003", datatype="float32",
        scale=0.01, unit="kPa",
    )
    value, unit = conv.convert(5000, "raw", entry.unit, entry.scale, entry.offset)
    assert value == pytest.approx(50.0)
    assert unit == "kPa"


def test_per_tag_calibration_skips_dictionary(conv: UnitConverter) -> None:
    """scale/offset из карты — калибровка, conversion-словарь не применяется."""
    entry = TagMapEntry(
        native_id="HR1", tag_id="PAI3004", datatype="float32",
        scale=1.0, offset=5.0, unit="bar",
    )
    value, unit = conv.convert(10.0, "kPa", entry.unit, entry.scale, entry.offset)
    assert value == pytest.approx(15.0)  # 10*1 + 5, не 0.1
    assert unit == "bar"


# =============================================================================
# AC-B4-09 — unknown unit → unit=unknown + warning
# =============================================================================


def test_unknown_from_unit_returns_unknown_with_warning(
    conv: UnitConverter, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="collector.core.unit_converter"):
        value, unit = conv.convert(20.0, "fluxcapacitor", "degC")
    assert value == 20.0  # value passed through
    assert unit == "unknown"
    assert any("fluxcapacitor" in rec.message for rec in caplog.records)


def test_no_conversion_rule_returns_unknown_with_warning(
    conv: UnitConverter, caplog: pytest.LogCaptureFixture
) -> None:
    """Известные единицы, но нет правила bar→degC."""
    with caplog.at_level(logging.WARNING, logger="collector.core.unit_converter"):
        value, unit = conv.convert(1.0, "bar", "degC")
    assert value == 1.0
    assert unit == "unknown"
    assert len(caplog.records) == 1


# =============================================================================
# Non-numeric passthrough
# =============================================================================


def test_none_passthrough(conv: UnitConverter) -> None:
    value, unit = conv.convert(None, "degC", "K")
    assert value is None
    assert unit == "K"


def test_bool_passthrough(conv: UnitConverter) -> None:
    value, unit = conv.convert(True, "bool", "bool")
    assert value is True
    assert unit == "bool"


def test_string_passthrough(conv: UnitConverter) -> None:
    value, unit = conv.convert("OPEN", "state", "state")
    assert value == "OPEN"
    assert unit == "state"


def test_nan_passthrough_not_converted(conv: UnitConverter) -> None:
    """NaN не преобразуется — QualityEngine (s11) отвечает за non-finite→bad."""
    value, unit = conv.convert(float("nan"), "degC", "K")
    import math
    assert math.isnan(value)
    assert unit == "K"


# =============================================================================
# from_yaml (canon + reload)
# =============================================================================


def test_from_yaml_loads_canon_round_trip() -> None:
    conv = UnitConverter.from_yaml(CANON_YAML)
    # degC→K должно работать с canon-файлом
    value, unit = conv.convert(0.0, "degC", "K")
    assert value == pytest.approx(273.15)
    assert unit == "K"


def test_reload_new_instance_applies_edited_rule(tmp_path: Path) -> None:
    f1 = tmp_path / "u1.yaml"
    f1.write_text(
        "version: 1\naliases: {}\nconversions:\n"
        "  - {from: degC, to: K, scale: 1.0, offset: 273.15}\n",
        encoding="utf-8",
    )
    c1 = UnitConverter.from_yaml(f1)
    assert c1.convert(0.0, "degC", "K")[0] == pytest.approx(273.15)

    f2 = tmp_path / "u2.yaml"
    f2.write_text(
        "version: 1\naliases: {}\nconversions:\n"
        "  - {from: degC, to: K, scale: 1.0, offset: 999.0}\n",
        encoding="utf-8",
    )
    c2 = UnitConverter.from_yaml(f2)
    assert c2.convert(0.0, "degC", "K")[0] == pytest.approx(999.0)
