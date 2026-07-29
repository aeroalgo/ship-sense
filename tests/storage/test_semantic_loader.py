"""s12 — Semantic loader: load ship-pack YAML, fail-fast validation, checksum.

Behavioural tests through public `load_pack(pack_dir)` interface.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from apps.edge.semantic.loader import SemanticPackError, load_pack


# --------------------------------------------------------------------------- #
# Fixtures: minimal valid 5-tag pack (aps_main + skt_geu)
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

# 6 tags total (4+1+1) but sources expect 4+2=6 -> ok
# fix sources to 4 + 2 to match assets count below
TAG_MAP_YAML = """\
tags:
  TAI4101:
    label: "Темп подшипника GD1 DE"
    unit: degC
    source_id: aps_main
    signal_type: analog
    range: {min: 0, max: 150}
    setpoints: {warn: 75, alarm: 85}
  TAI4102:
    label: "Темп подшипника GD1 NDE"
    unit: degC
    source_id: aps_main
    signal_type: analog
  PAL4102:
    label: "Высокая темп GD1"
    unit: bool
    source_id: aps_main
    signal_type: alarm_bit
    alarm_class: critical
  PAL4103:
    label: "Критическая темп GD1"
    unit: bool
    source_id: aps_main
    signal_type: alarm_bit
    alarm_class: critical
  TAI4201:
    label: "Темп морской воды"
    unit: degC
    source_id: aps_main
    signal_type: analog
  SKT001:
    label: "Обороты ГЭУ"
    unit: rpm
    source_id: skt_geu
    signal_type: analog
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


def _write_pack(tmp: Path, vessel=VESSEL_YAML, assets=ASSETS_YAML,
                tag_map=TAG_MAP_YAML, native=NATIVE_MAP_YAML) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "vessel.yaml").write_text(vessel, encoding="utf-8")
    (tmp / "assets.yaml").write_text(assets, encoding="utf-8")
    (tmp / "tag_map.yaml").write_text(tag_map, encoding="utf-8")
    if native is not None:
        (tmp / "native_map_stub.yaml").write_text(native, encoding="utf-8")
    return tmp


# --------------------------------------------------------------------------- #
# Happy path
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("marker", ["semantic_loader"])
def test_load_minimal_pack_ok(tmp_path: Path, marker: str) -> None:
    pack = load_pack(_write_pack(tmp_path))

    assert pack.vessel_id == "makarov"
    assert pack.name == "Адмирал Макаров"
    assert pack.pack_version == "1.0.0-emulator"
    assert [s.id for s in pack.sources] == ["aps_main", "skt_geu"]
    assert len(pack.tags) == 6
    # tree root = vessel node; two engine rooms
    assert pack.root.kind.value == "vessel"
    assert [er.id for er in pack.root.children] == ["NDO", "GDU"]
    # mechanism tags reachable
    gd1 = pack.root.children[0].children[0].children[0]
    assert gd1.kind.value == "mechanism"
    assert gd1.tags == ["TAI4101", "TAI4102", "PAL4102", "PAL4103"]
    # checksum present and hex sha256 length
    assert len(pack.checksum) == 64
    assert int(pack.checksum, 16) >= 0


def test_tag_meta_fields_parsed(tmp_path: Path) -> None:
    pack = load_pack(_write_pack(tmp_path))
    t = pack.tags["TAI4101"]
    assert t.label == "Темп подшипника GD1 DE"
    assert t.unit == "degC"
    assert t.source_id == "aps_main"
    assert t.signal_type.value == "analog"
    assert t.range is not None and t.range.min == 0 and t.range.max == 150
    assert t.setpoints is not None and t.setpoints.alarm == 85
    alarm = pack.tags["PAL4102"]
    assert alarm.alarm_class is not None and alarm.alarm_class.value == "critical"


def test_native_map_parsed(tmp_path: Path) -> None:
    pack = load_pack(_write_pack(tmp_path))
    assert pack.native_map is not None
    assert pack.native_map.version == "stub-0.1"
    assert pack.native_map.approved is True
    assert {m.tag_id for m in pack.native_map.mappings} == {"TAI4101", "TAI4102"}


def test_native_map_optional(tmp_path: Path) -> None:
    pack = load_pack(_write_pack(tmp_path, native=None))
    assert pack.native_map is None


def test_checksum_deterministic(tmp_path: Path) -> None:
    a = load_pack(_write_pack(tmp_path / "a"))
    b = load_pack(_write_pack(tmp_path / "b"))
    assert a.checksum == b.checksum


# --------------------------------------------------------------------------- #
# Fail-fast validation
# --------------------------------------------------------------------------- #

def test_duplicate_tag_across_mechanisms_raises(tmp_path: Path) -> None:
    bad = ASSETS_YAML.replace("tags: [TAI4201]", "tags: [TAI4101]")  # TAI4101 appears twice
    # drop TAI4201 from tag_map so counts stay consistent (aps_main now 4)
    tag_map = TAG_MAP_YAML.replace(
        """  TAI4201:
    label: "Темп морской воды"
    unit: degC
    source_id: aps_main
    signal_type: analog
""", "")
    vessel = VESSEL_YAML.replace("tag_count_expected: 5", "tag_count_expected: 4")
    with pytest.raises(SemanticPackError) as exc:
        load_pack(_write_pack(tmp_path, vessel=vessel, assets=bad, tag_map=tag_map))
    assert "assets.yaml" in str(exc.value)
    assert "TAI4101" in str(exc.value)


def test_duplicate_tag_key_in_tag_map_raises_with_line(tmp_path: Path) -> None:
    bad = TAG_MAP_YAML + """\
  TAI4101:
    label: "дубль"
    unit: degC
    source_id: aps_main
    signal_type: analog
"""
    with pytest.raises(SemanticPackError) as exc:
        load_pack(_write_pack(tmp_path, tag_map=bad))
    assert "tag_map.yaml" in str(exc.value)
    assert "TAI4101" in str(exc.value)
    # line number present
    assert exc.value.line is not None and exc.value.line > 1


def test_orphan_tag_in_tag_map_raises(tmp_path: Path) -> None:
    bad = TAG_MAP_YAML + """\
  GHOST001:
    label: "нет в assets"
    unit: degC
    source_id: aps_main
    signal_type: analog
"""
    # bump expected to account for the extra orphan tag
    vessel = VESSEL_YAML.replace("tag_count_expected: 5", "tag_count_expected: 6")
    with pytest.raises(SemanticPackError) as exc:
        load_pack(_write_pack(tmp_path, vessel=vessel, tag_map=bad))
    assert "GHOST001" in str(exc.value)


def test_tag_in_assets_not_in_tag_map_raises(tmp_path: Path) -> None:
    # remove SKT001 from tag_map
    bad = TAG_MAP_YAML.replace(
        """  SKT001:
    label: "Обороты ГЭУ"
    unit: rpm
    source_id: skt_geu
    signal_type: analog
""", "")
    vessel = VESSEL_YAML.replace("tag_count_expected: 1", "tag_count_expected: 0")
    with pytest.raises(SemanticPackError) as exc:
        load_pack(_write_pack(tmp_path, vessel=vessel, tag_map=bad))
    assert "SKT001" in str(exc.value)


def test_invalid_source_ref_raises(tmp_path: Path) -> None:
    bad = TAG_MAP_YAML.replace("source_id: skt_geu", "source_id: nonexistent")
    with pytest.raises(SemanticPackError) as exc:
        load_pack(_write_pack(tmp_path, tag_map=bad))
    assert "nonexistent" in str(exc.value)


def test_count_mismatch_raises(tmp_path: Path) -> None:
    vessel = VESSEL_YAML.replace("tag_count_expected: 5", "tag_count_expected: 99")
    with pytest.raises(SemanticPackError) as exc:
        load_pack(_write_pack(tmp_path, vessel=vessel))
    assert "count" in str(exc.value).lower() or "expected" in str(exc.value).lower()


def test_native_map_orphan_is_warning_not_error(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    bad = NATIVE_MAP_YAML.replace("tag_id: TAI4102", "tag_id: ORPHAN999")
    import logging
    with caplog.at_level(logging.WARNING):
        pack = load_pack(_write_pack(tmp_path, native=bad))
    # pack loads successfully
    assert pack.native_map is not None
    assert any("ORPHAN999" in r.message for r in caplog.records)


def test_missing_required_yaml_raises(tmp_path: Path) -> None:
    (tmp_path / "vessel.yaml").write_text(VESSEL_YAML)
    # no assets.yaml / tag_map.yaml
    with pytest.raises(SemanticPackError):
        load_pack(tmp_path)


def test_native_map_duplicate_native_id_raises(tmp_path: Path) -> None:
    bad = NATIVE_MAP_YAML + """\
  - native_id: "MODBUS:40001"
    tag_id: TAI4101
    codec: float32
"""
    with pytest.raises(SemanticPackError) as exc:
        load_pack(_write_pack(tmp_path, native=bad))
    assert "MODBUS:40001" in str(exc.value)
