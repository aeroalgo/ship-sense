from pathlib import Path

import pytest

from collector.config.loader import load_sources, load_tag_map
from collector.config.validator import validate_config
from collector.domain.errors import ConfigError


VALID_SOURCES = """
version: 1
sources:
  - id: aps_main
    protocol: modbus_tcp
    endpoint: emulator:5020
    poll:
      default_hz: 1.0
      groups:
        - name: analog_fast
          hz: 1.0
    tag_map_ref: maps/aps.yaml
    readonly_profile: true
  - id: skt_geu
    protocol: modbus_tcp
    endpoint: emulator:5021
    poll:
      default_hz: 1.0
    tag_map_ref: maps/skt.yaml
    readonly_profile: true
"""


VALID_MAP = """
version: 1
source_id: aps_main
tags:
  - native_id: '40101'
    tag_id: TAI4101
    type: float32
    unit: degC
    range: {min: -40, max: 120}
  - native_id: '40200.3'
    tag_id: XA1201
    type: bit
    fc: 4
"""


def write_config_tree(tmp_path: Path) -> Path:
    config_path = tmp_path / "sources.yaml"
    config_path.write_text(VALID_SOURCES, encoding="utf-8")
    maps_dir = tmp_path / "maps"
    maps_dir.mkdir()
    (maps_dir / "aps.yaml").write_text(VALID_MAP, encoding="utf-8")
    (maps_dir / "skt.yaml").write_text(
        VALID_MAP.replace("aps_main", "skt_geu"), encoding="utf-8"
    )
    return config_path


def test_valid_config_loads_and_validates(tmp_path: Path) -> None:
    config_path = write_config_tree(tmp_path)

    sources = load_sources(config_path)

    assert [source.id for source in sources] == ["aps_main", "skt_geu"]
    assert sources[0].poll is not None
    assert sources[0].poll.groups[0].name == "analog_fast"
    assert validate_config(sources, tmp_path / "maps") == sources


def test_duplicate_native_id_is_rejected(tmp_path: Path) -> None:
    config_path = write_config_tree(tmp_path)
    duplicate_map = VALID_MAP.replace("'40200.3'", "'40101'")
    (tmp_path / "maps" / "aps.yaml").write_text(duplicate_map, encoding="utf-8")

    with pytest.raises(ConfigError, match="duplicate native_id.*40101"):
        validate_config(load_sources(config_path), tmp_path / "maps")


def test_missing_map_reference_is_rejected(tmp_path: Path) -> None:
    config_path = write_config_tree(tmp_path)
    config_path.write_text(VALID_SOURCES.replace("maps/skt.yaml", "maps/missing.yaml"), encoding="utf-8")

    with pytest.raises(ConfigError, match="missing map"):
        validate_config(load_sources(config_path), tmp_path / "maps")


def test_environment_paths_override_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = write_config_tree(tmp_path)
    monkeypatch.setenv("COLLECTOR_SOURCES_PATH", str(config_path))
    monkeypatch.setenv("COLLECTOR_MAPS_DIR", str(tmp_path / "maps"))

    assert [source.id for source in load_sources()] == ["aps_main", "skt_geu"]
    assert validate_config() == load_sources(config_path)


def test_load_tag_map_normalizes_type_and_range(tmp_path: Path) -> None:
    map_path = tmp_path / "map.yaml"
    map_path.write_text(VALID_MAP, encoding="utf-8")

    entries = load_tag_map(map_path)

    assert entries[0].datatype == "float32"
    assert entries[0].range_min == -40
    assert entries[0].range_max == 120
    assert entries[1].fc == 4


def test_import_interfaces_without_circular_dependency() -> None:
    import subprocess
    import sys
    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent / "src")
    result = subprocess.run(
        [sys.executable, "-c", "import collector.domain.interfaces"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Import failed:\n{result.stderr}"
