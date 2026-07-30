"""s13 — SemanticEngine TDD tests (RED first).

Behaviour through public API after load(pack_dir).
Uses small valid pack from s12 fixtures (6 tags).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.semantic.loader import load_pack
from app.semantic.models import (
    AggregateStatus,
    NativeMap,
    NativeMapMapping,
    QuarantineReport,
    TagDisplayState,
)
from app.semantic.engine import SemanticEngine


# --------------------------------------------------------------------------- #
# Minimal pack fixtures (copy of loader test pack for self-contained)
# --------------------------------------------------------------------------- #

VESSEL_YAML = """\
vessel:
  id: makarov
  name: "Адмирал Макаров"
  imo: "XXXXXXX"
  pack_version: "1.0.0-emulator"
sources:
  - id: aps_main
    label: "АПС"
    tag_count_expected: 5
  - id: skt_geu
    label: "СКТ ГЭУ"
    tag_count_expected: 1
"""

ASSETS_YAML = """\
engine_rooms:
  - id: NDO
    label: "Носовое МО"
    systems:
      - id: lube_oil
        label: "Система смазки"
        mechanisms:
          - id: GD1
            label: "ГД №1"
            tags: [TAI4101, TAI4102, PAL4102, PAL4103]
      - id: cooling
        label: "Система охлаждения"
        mechanisms:
          - id: CW_PUMP_1
            label: "Морской насос №1"
            tags: [TAI4201]
  - id: GDU
    label: "ГДУ / СКТ"
    systems:
      - id: skt_monitor
        label: "СКТ ГЭУ"
        mechanisms:
          - id: GEU_1
            label: "ГЭУ"
            tags: [SKT001]
"""

TAG_MAP_YAML = """\
tags:
  TAI4101:
    label: "Темп подшипника GD1 DE"
    unit: degC
    source_id: aps_main
    signal_type: analog
    expected_rate_s: 1.0
  TAI4102:
    label: "Темп подшипника GD1 NDE"
    unit: degC
    source_id: aps_main
    signal_type: analog
    expected_rate_s: 1.0
  PAL4102:
    label: "Давление масла ГД1"
    unit: bar
    source_id: aps_main
    signal_type: analog
    expected_rate_s: 1.0
  PAL4103:
    label: "Давление масла ГД1 (дубль)"
    unit: bar
    source_id: aps_main
    signal_type: analog
    expected_rate_s: 1.0
  TAI4201:
    label: "Темп забортной воды"
    unit: degC
    source_id: aps_main
    signal_type: analog
    expected_rate_s: 5.0
  SKT001:
    label: "Обороты ГЭУ"
    unit: rpm
    source_id: skt_geu
    signal_type: analog
    expected_rate_s: 0.1
"""

NATIVE_MAP_YAML = """\
version: stub-0.1
approved: true
mappings:
  - native_id: "MODBUS:40001"
    tag_id: TAI4101
    codec: float32
    byte_order: big_endian
  - native_id: "MODBUS:40002"
    tag_id: TAI4102
    codec: float32
    byte_order: big_endian
"""


def _write_pack(tmp: Path, *, vessel=VESSEL_YAML, assets=ASSETS_YAML,
                tag_map=TAG_MAP_YAML, native=NATIVE_MAP_YAML) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "vessel.yaml").write_text(vessel, encoding="utf-8")
    (tmp / "assets.yaml").write_text(assets, encoding="utf-8")
    (tmp / "tag_map.yaml").write_text(tag_map, encoding="utf-8")
    if native is not None:
        (tmp / "native_map_stub.yaml").write_text(native, encoding="utf-8")
    return tmp


# --------------------------------------------------------------------------- #
# Helpers for time control in tests
# --------------------------------------------------------------------------- #

NOW = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _mk_engine(pack_dir: Path) -> SemanticEngine:
    eng = SemanticEngine(now_provider=lambda: NOW)
    eng.load(pack_dir)
    return eng


# --------------------------------------------------------------------------- #
# Happy load + navigation
# --------------------------------------------------------------------------- #

def test_load_and_navigation(tmp_path: Path) -> None:
    pack_dir = _write_pack(tmp_path)
    eng = _mk_engine(pack_dir)

    tree = eng.get_tree()
    assert tree.kind.value == "vessel"
    assert tree.id == "<vessel>"  # synthetic root per loader
    assert len(tree.children) == 2  # NDO, GDU

    meta = eng.get_tag_meta("TAI4101")
    assert meta.unit == "degC"
    assert meta.source_id == "aps_main"
    assert meta.expected_rate_s == 1.0

    mech_tags = eng.get_mechanism_tags("GD1")
    assert set(mech_tags) == {"TAI4101", "TAI4102", "PAL4102", "PAL4103"}

    mech_tags2 = eng.get_mechanism_tags("GEU_1")
    assert mech_tags2 == ["SKT001"]


# --------------------------------------------------------------------------- #
# aggregate_status worst-of
# --------------------------------------------------------------------------- #

def test_aggregate_status_normal(tmp_path: Path) -> None:
    eng = _mk_engine(_write_pack(tmp_path))
    # seed fresh samples for ALL tags -> full normal tree
    for t in list(eng._tags.keys()):
        eng.update_last_sample_ts(t, NOW - timedelta(seconds=1))
    assert eng.aggregate_status("GD1") == AggregateStatus.NORMAL
    assert eng.aggregate_status("NDO") == AggregateStatus.NORMAL
    assert eng.aggregate_status("<vessel>") == AggregateStatus.NORMAL


def test_aggregate_status_quarantine_worst(tmp_path: Path) -> None:
    pack_dir = _write_pack(tmp_path)
    eng = _mk_engine(pack_dir)

    # seed fresh for the rest so only the quarantined one drives worst
    for t in ["TAI4101", "TAI4102", "PAL4102", "PAL4103"]:
        eng.update_last_sample_ts(t, NOW - timedelta(seconds=1))
    eng._quarantined.add("TAI4101")  # test hook for s13 (in-mem only)
    assert eng.aggregate_status("GD1") == AggregateStatus.QUARANTINE
    # parent aggregates
    assert eng.aggregate_status("NDO") == AggregateStatus.QUARANTINE
    assert eng.aggregate_status("<vessel>") == AggregateStatus.QUARANTINE


def test_aggregate_status_no_data_worst(tmp_path: Path) -> None:
    pack_dir = _write_pack(tmp_path)
    eng = _mk_engine(pack_dir)

    # seed one tag fresh, leave the rest without samples -> worst = no_data
    eng.update_last_sample_ts("TAI4101", NOW - timedelta(seconds=1))
    assert eng.aggregate_status("GD1") == AggregateStatus.NO_DATA


# --------------------------------------------------------------------------- #
# get_tag_state precedence (stop > quarantine > no_data > stale > normal)
# --------------------------------------------------------------------------- #

def test_get_tag_state_normal_when_fresh(tmp_path: Path) -> None:
    eng = _mk_engine(_write_pack(tmp_path))
    # age < stale_threshold (3s for 1Hz tag) -> normal
    eng.update_last_sample_ts("TAI4101", NOW - timedelta(seconds=1))
    assert eng.get_tag_state("TAI4101") == TagDisplayState.NORMAL


def test_get_tag_state_stale(tmp_path: Path) -> None:
    eng = _mk_engine(_write_pack(tmp_path))
    # expected_rate_s=1.0 -> stale_threshold ~3s, here 10s old
    eng.update_last_sample_ts("TAI4101", NOW - timedelta(seconds=10))
    assert eng.get_tag_state("TAI4101") == TagDisplayState.STALE


def test_get_tag_state_no_data(tmp_path: Path) -> None:
    eng = _mk_engine(_write_pack(tmp_path))
    # no update ever, or very old (> no_data_window ~90s for 1Hz)
    # use a tag with expected 1s
    assert eng.get_tag_state("TAI4101") == TagDisplayState.NO_DATA

    # old but within no_data window? no -> stale first
    eng.update_last_sample_ts("TAI4101", NOW - timedelta(seconds=40))
    assert eng.get_tag_state("TAI4101") == TagDisplayState.STALE

    # beyond no_data
    eng.update_last_sample_ts("TAI4101", NOW - timedelta(seconds=100))
    assert eng.get_tag_state("TAI4101") == TagDisplayState.NO_DATA


def test_get_tag_state_quarantine_unacked(tmp_path: Path) -> None:
    pack_dir = _write_pack(tmp_path)
    eng = _mk_engine(pack_dir)
    eng.update_last_sample_ts("TAI4101", NOW)
    eng._quarantined.add("TAI4101")
    assert eng.get_tag_state("TAI4101") == TagDisplayState.QUARANTINE

    # acknowledged clears it (via public API)
    eng.acknowledge_quarantine("TAI4101")
    assert "TAI4101" not in eng._quarantined
    assert eng.get_tag_state("TAI4101") == TagDisplayState.NORMAL


def test_get_tag_state_stop_not_reached_on_valid_load(tmp_path: Path) -> None:
    eng = _mk_engine(_write_pack(tmp_path))
    # stop is only for global invalid pack; load path does not set it
    assert eng.get_tag_state("TAI4101") in (TagDisplayState.NORMAL, TagDisplayState.NO_DATA, TagDisplayState.STALE)


# --------------------------------------------------------------------------- #
# diff_native_map + quarantine report
# --------------------------------------------------------------------------- #

def test_diff_native_map_added(tmp_path: Path) -> None:
    eng = _mk_engine(_write_pack(tmp_path))

    # new native mapping to unknown tag -> added + quarantine candidate
    new_map = NativeMap(
        version="live-1",
        approved=False,
        mappings=[
            NativeMapMapping(native_id="MODBUS:99999", tag_id="GHOST999", codec="float32"),
        ],
    )
    report = eng.diff_native_map(new_map)
    assert isinstance(report, QuarantineReport)
    assert len(report.added) == 1
    assert report.added[0].kind.value == "added"
    assert "GHOST999" in report.added[0].reason or "native_to_unknown" in report.added[0].reason
    # unknown tag reported but NOT put into quarantine cache (only real tags get QUARANTINE state)
    assert "GHOST999" not in eng.quarantined_tags
    # for unknown tag_id get_tag_state is NO_DATA (not QUARANTINE)
    assert eng.get_tag_state("GHOST999") == TagDisplayState.NO_DATA


def test_diff_native_map_removed_and_changed(tmp_path: Path) -> None:
    eng = _mk_engine(_write_pack(tmp_path))

    # approved had TAI4101 + TAI4102; now remove one, remap another
    new_map = NativeMap(
        version="live-1",
        approved=False,
        mappings=[
            # TAI4101 removed -> removed entry
            # TAI4102 remapped to different tag
            NativeMapMapping(native_id="MODBUS:40002", tag_id="TAI4201", codec="float32"),
        ],
    )
    report = eng.diff_native_map(new_map)
    # at least one removed or changed
    assert len(report.removed) + len(report.changed) >= 1


def test_diff_native_map_no_change_when_same(tmp_path: Path) -> None:
    eng = _mk_engine(_write_pack(tmp_path))
    # use the original approved map
    orig = load_pack(_write_pack(tmp_path)).native_map
    assert orig is not None
    report = eng.diff_native_map(orig)
    assert len(report.added) == 0
    assert len(report.removed) == 0
    assert len(report.changed) == 0


# --------------------------------------------------------------------------- #
# acknowledge clears quarantine state
# --------------------------------------------------------------------------- #

def test_acknowledge_clears_quarantine_state(tmp_path: Path) -> None:
    pack_dir = _write_pack(tmp_path)
    eng = _mk_engine(pack_dir)
    eng._quarantined.add("PAL4102")
    assert eng.get_tag_state("PAL4102") == TagDisplayState.QUARANTINE
    eng.acknowledge_quarantine("PAL4102")
    assert eng.get_tag_state("PAL4102") != TagDisplayState.QUARANTINE
