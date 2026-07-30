"""s22 — Integration: all dirt scenarios through B4 (AC-I3-04..13, AC-B4-13).

Связывает I3 (dirt injectors эмулятора) с B4 (Normalizer pipeline): каждый dirt
scenario оставляет в RawSample характерную сигнатуру (значение / native_quality /
timestamp), и B4 обязан корректно отобразить её в Quality — не падая (AC-B4-13).

Не поднимает live TCP (это s19/s20/s21); гоняет реальный Normalizer.process() с
синтезированными RawSample, воспроизводящими сигнатуры грязи. Матрица:
scenario → ожидаемый quality/behavior по AC-I3-04..13.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from collector.config.models import TagMapEntry
from collector.core.event_detector import EventDetector
from collector.core.normalizer import Normalizer
from collector.core.quality_engine import QualityEngine
from collector.core.unit_converter import UnitConverter, UnitRules
from app.telemetry.models import Quality
from collector.domain.raw_models import RawSample

EDGE_NOW = datetime(2026, 7, 27, 12, 0, tzinfo=timezone.utc)
QUALITY_RULES = "apps/edge/collector/config/quality_rules.yaml"


def _entry(
    *,
    native_id: str = "40101",
    tag_id: str = "TAI4101",
    datatype: str = "float",
    unit: str | None = "degC",
    range_min: float | None = 0.0,
    range_max: float | None = 100.0,
) -> TagMapEntry:
    return TagMapEntry(
        native_id=native_id,
        tag_id=tag_id,
        datatype=datatype,
        unit=unit,
        range_min=range_min,
        range_max=range_max,
    )


def _raw(
    *,
    native_id: str = "40101",
    value: object = 50.0,
    source_id: str = "aps_main",
    source_ts: datetime | None = EDGE_NOW,
    native_quality: str | None = None,
    recv_ts: datetime = EDGE_NOW,
) -> RawSample:
    return RawSample(
        source_id=source_id,
        native_id=native_id,
        raw_value=value,
        native_quality=native_quality,
        recv_ts=recv_ts,
        source_ts=source_ts,
    )


def _normalizer(
    *,
    entries: dict[str, TagMapEntry] | None = None,
    with_events: bool = False,
) -> Normalizer:
    return Normalizer(
        tag_map=entries if entries is not None else {"40101": _entry()},
        quality_engine=QualityEngine.from_yaml(QUALITY_RULES),
        unit_converter=UnitConverter(UnitRules()),
        event_detector=EventDetector() if with_events else None,
        now_fn=lambda: EDGE_NOW,
    )


# ---------------------------------------------------------------------------
# Матрица: dirt scenario → quality через B4 (AC-I3-04..13)
# ---------------------------------------------------------------------------

# Сигнатура грязи в RawSample, как её кодирует connector на пути из эмулятора,
# и ожидаемый Quality, который ставит B4. AC-I3-04/09 — поведенческие (не quality),
# проверяются отдельными тестами ниже; сюда входят только quality-маппинги.
QUALITY_MATRIX: list[tuple[str, RawSample, Quality]] = [
    # AC-I3-05 connection_drop → Modbus timeout → bad
    ("connection_drop", _raw(native_quality="modbus.timeout"), Quality.BAD),
    # AC-I3-12 modbus_bad_frame → Modbus exception → bad
    ("modbus_bad_frame", _raw(native_quality="modbus.exception.4"), Quality.BAD),
    # AC-I3-13 opc_bad_quality → Bad StatusCode → bad
    ("opc_bad_quality", _raw(native_quality="opcua.BadNoCommunication"), Quality.BAD),
    # AC-I3-08 nan_inf → NaN/Inf → bad, value null (AC-B4-08)
    ("nan_inf", _raw(value=float("nan")), Quality.BAD),
    ("inf", _raw(value=float("inf")), Quality.BAD),
    # AC-I3-06 out_of_range → uncertain, значение сохраняется (AC-B4-07)
    ("out_of_range_high", _raw(value=150.0), Quality.UNCERTAIN),
    ("out_of_range_low", _raw(value=-10.0), Quality.UNCERTAIN),
    # AC-I3-07 stuck_value + устаревший timestamp → stale по правилам B4
    (
        "stuck_value_stale",
        _raw(value=50.0, source_ts=EDGE_NOW - timedelta(seconds=10)),
        Quality.STALE,
    ),
    # AC-I3-09 time_jump в прошлое → stale (аномальный age)
    (
        "time_jump_past",
        _raw(value=50.0, source_ts=EDGE_NOW - timedelta(hours=1)),
        Quality.STALE,
    ),
    # clean baseline → good
    ("baseline", _raw(value=50.0), Quality.GOOD),
]


@pytest.mark.parametrize("scenario,raw,expected_quality", QUALITY_MATRIX)
def test_dirt_scenario_maps_to_expected_quality(
    scenario: str,
    raw: RawSample,
    expected_quality: Quality,
) -> None:
    # AC-B4-13: normalizer не падает ни на одном сценарии грязи.
    sample = _normalizer().process(raw)

    assert sample is not None, f"{scenario}: normalizer вернул None (упал/дропнул)"
    assert sample.quality is expected_quality, (
        f"{scenario}: ожидали {expected_quality.value}, получили {sample.quality.value}"
    )


@pytest.mark.parametrize("scenario", ["nan_inf", "inf"])
def test_dirt_nan_inf_value_is_nulled(scenario: str) -> None:
    # AC-B4-08: NaN/Inf → bad, value null.
    raw = _raw(value=float(scenario.replace("nan_inf", "nan").replace("inf", "inf")))
    sample = _normalizer().process(raw)

    assert sample is not None
    assert sample.quality is Quality.BAD
    assert sample.value is None


@pytest.mark.parametrize("value", [150.0, -10.0])
def test_dirt_out_of_range_keeps_value(value: float) -> None:
    # AC-B4-07: out-of-range → uncertain, значение сохраняется.
    sample = _normalizer().process(_raw(value=value))

    assert sample is not None
    assert sample.quality is Quality.UNCERTAIN
    assert sample.value == value


# ---------------------------------------------------------------------------
# AC-I3-06 connection_drop: native quality «bad» → value null (не valid number)
# ---------------------------------------------------------------------------


def test_connection_drop_and_bad_frame_null_value() -> None:
    normalizer = _normalizer()
    # Различные source_ts — иначе B4 dedup (AC-I3-11) дропает повторы.
    for i, token in enumerate(
        ("modbus.timeout", "modbus.client_error", "modbus.exception.4")
    ):
        sample = normalizer.process(
            _raw(native_quality=token, value=50.0, source_ts=EDGE_NOW + timedelta(i))
        )
        assert sample is not None
        assert sample.quality is Quality.BAD, f"{token}: ожидали bad"
        assert sample.value is None, f"{token}: bad должен нулить value"


# ---------------------------------------------------------------------------
# AC-I3-09 time_jump в будущее → не падает, age отрицательный → good (не stale)
# ---------------------------------------------------------------------------


def test_time_jump_future_does_not_crash() -> None:
    sample = _normalizer().process(_raw(source_ts=EDGE_NOW + timedelta(hours=1)))

    assert sample is not None
    assert sample.quality is Quality.GOOD  # age < 0, не stale


# ---------------------------------------------------------------------------
# AC-I3-10 tag_map_change: неизвестный NodeId → quarantine downstream
# ---------------------------------------------------------------------------


def test_tag_map_change_unknown_node_is_quarantined() -> None:
    sample = _normalizer(entries={}).process(
        _raw(native_id="ns=2;s=DIRT0001", value=1)
    )

    assert sample is not None
    assert sample.quality is Quality.QUARANTINE
    assert sample.tag_id == "ns=2;s=DIRT0001"  # fallback на native_id
    assert sample.value is None
    assert sample.unit == "unknown"


# ---------------------------------------------------------------------------
# AC-I3-11 duplicate_delivery → idempotent B4 (второй сэмпл дропается)
# ---------------------------------------------------------------------------


def test_duplicate_delivery_is_idempotent() -> None:
    normalizer = _normalizer()
    raw = _raw(value=50.0, source_ts=EDGE_NOW)

    first = normalizer.process(raw)
    second = normalizer.process(raw)

    assert first is not None
    assert first.quality is Quality.GOOD
    assert second is None, "дубликат должен дропаться (dedup по native_id+source_ts)"


# ---------------------------------------------------------------------------
# AC-I3-04 signal_chatter: дребезг дискретного сигнала — несколько быстрых
# изменений bool не роняют normalizer; discrete обрабатывается через events.
# ---------------------------------------------------------------------------


def test_signal_chatter_discrete_stream_does_not_crash() -> None:
    normalizer = _normalizer(
        entries={"40101": _entry(datatype="bool", range_min=None, range_max=None)},
        with_events=True,
    )
    values = [True, False, True, False, True]

    samples = [normalizer.process(_raw(value=v, source_ts=EDGE_NOW + timedelta(i))) for i, v in enumerate(values)]

    assert all(s is not None for s in samples)
    assert all(s.quality is Quality.GOOD for s in samples)
    # Chatter = серия discrete-change events; B4 их эмитит без падения.
    events = normalizer.drain_events()
    assert events, "chatter должен порождать discrete-change events"


# ---------------------------------------------------------------------------
# AC-B4-13 (итог): полная матрица грязи — ни одного uncaught exception.
# ---------------------------------------------------------------------------


def test_all_dirt_scenarios_do_not_raise() -> None:
    normalizer = _normalizer()
    dirty_payloads = [
        _raw(value=float("nan")),
        _raw(value=float("inf")),
        _raw(value=150.0),
        _raw(value=-10.0, native_id="40101"),
        _raw(native_quality="modbus.timeout"),
        _raw(native_quality="opcua.BadNoCommunication"),
        _raw(source_ts=EDGE_NOW - timedelta(hours=2)),
        _raw(native_id="ns=2;s=UNKNOWN"),
    ]

    for raw in dirty_payloads:
        # Не assert на качество здесь (покрыто матрицей) — только «не роняет».
        normalizer.process(raw)
