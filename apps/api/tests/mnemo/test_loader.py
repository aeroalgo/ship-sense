from pathlib import Path

import pytest

from app.mnemo.loader import MnemoConfigError, MnemoBindingLoader


PACK_ROOT = Path(__file__).parents[4] / "ship-pack" / "makarov"


def test_loads_mvp_schema_with_value_enum_and_computed_bindings() -> None:
    registry = MnemoBindingLoader().load_all(PACK_ROOT)

    schema = registry["engine_diesel_main"]
    assert schema.revision == 3
    assert {element.bind_type for element in schema.elements} == {
        "value",
        "enum",
        "computed",
    }
    assert schema.computed_bindings["exhaust_temp_deviation"].type == "sibling_mean_delta"


def test_rejects_value_without_tag_id(tmp_path: Path) -> None:
    _write_pack(tmp_path, """\
 schema_id: invalid
 screen: 2
 revision: 1
 svg:
   file: mnemo/invalid.svg
   viewBox: 0 0 1 1
 elements:
   - element_id: value
     bind_type: value
     display:
       format: '{:.0f}'
 """)

    with pytest.raises(MnemoConfigError, match="invalid.yaml"):
        MnemoBindingLoader().load_all(tmp_path)


def test_rejects_schema_filename_mismatch(tmp_path: Path) -> None:
    _write_pack(tmp_path, """\
 schema_id: other
 screen: 2
 revision: 1
 svg:
   file: mnemo/other.svg
   viewBox: 0 0 1 1
 elements:
   - element_id: value
     bind_type: value
     tag_id: TAI4101
 """, filename="invalid.yaml")

    with pytest.raises(MnemoConfigError, match="filename"):
        MnemoBindingLoader().load_all(tmp_path)


def test_rejects_unknown_tag_and_publishes_no_partial_snapshot(tmp_path: Path) -> None:
    _write_pack(tmp_path, """\
 schema_id: first
 screen: 2
 revision: 1
 svg:
   file: mnemo/first.svg
   viewBox: 0 0 1 1
 elements:
   - element_id: value
     bind_type: value
     tag_id: TAI4101
 """, filename="first.yaml")
    _write_pack(tmp_path, """\
 schema_id: second
 screen: 2
 revision: 1
 svg:
   file: mnemo/second.svg
   viewBox: 0 0 1 1
 elements:
   - element_id: value
     bind_type: value
     tag_id: DOES_NOT_EXIST
 """, filename="second.yaml")

    with pytest.raises(MnemoConfigError, match="DOES_NOT_EXIST"):
        MnemoBindingLoader().load_all(tmp_path)


def _write_pack(root: Path, content: str, *, filename: str = "invalid.yaml") -> None:
    (root / "tag_map.yaml").write_text(
        "tags:\n  TAI4101:\n    label: temperature\n    unit: degC\n",
        encoding="utf-8",
    )
    (root / "mnemo_bindings").mkdir(exist_ok=True)
    (root / "mnemo_bindings" / filename).write_text(content, encoding="utf-8")
