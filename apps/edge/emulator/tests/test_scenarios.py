from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from emulator.dirt.scenario_runner import ScenarioRunner
from emulator.tag_model import TagGenerator


PROFILE = {
    "id": "scenario-test",
    "tick_hz": 1.0,
    "signals": [
        {
            "signal_id": "LEVEL",
            "native_ids": {"opcua": "ns=2;s=LEVEL", "modbus": "40101"},
            "range": {"min": 0, "max": 100},
            "value_type": "float32",
            "generator": {"kind": "constant", "value": 50.0},
        },
        {
            "signal_id": "SWITCH",
            "native_ids": {"opcua": "ns=2;s=SWITCH"},
            "range": {"min": 0, "max": 1},
            "value_type": "boolean",
            "generator": {"kind": "constant", "value": False},
        },
    ],
}


CONFIG = {
    "scenarios": [
        {"name": "baseline", "enabled": True, "seed": 7, "injectors": []},
        {
            "name": "dirty",
            "enabled": False,
            "seed": 11,
            "injectors": [
                {"type": "out_of_range", "params": {"signal_ids": ["LEVEL"], "at_sec": 1, "duration_sec": 3}},
                {"type": "stuck_value", "params": {"signal_ids": ["LEVEL"], "at_sec": 1, "duration_sec": 3}},
                {"type": "nan_inf", "params": {"signal_ids": ["LEVEL"], "at_sec": 5, "duration_sec": 1, "value": "nan"}},
                {"type": "signal_chatter", "params": {"signal_ids": ["SWITCH"], "at_sec": 1, "duration_sec": 3, "frequency_hz": 10}},
                {"type": "time_jump", "params": {"at_sec": 1, "duration_sec": 3, "offset_sec": 3600}},
                {"type": "tag_map_change", "params": {"at_sec": 1, "duration_sec": 3, "add": ["ns=2;s=NEW"]}},
                {"type": "opc_bad_quality", "params": {"signal_ids": ["LEVEL"], "at_sec": 1, "duration_sec": 3}},
                {"type": "connection_drop", "params": {"protocol": "modbus_tcp", "at_sec": 1, "duration_sec": 3}},
                {"type": "modbus_bad_frame", "params": {"at_sec": 1, "duration_sec": 3}},
                {"type": "duplicate_delivery", "params": {"at_sec": 1, "duration_sec": 3}},
            ],
        },
    ]
}


def runner() -> ScenarioRunner:
    return ScenarioRunner(CONFIG, TagGenerator(seed=3, profile=PROFILE))


def test_scenario_is_enabled_by_name_and_tick_is_deterministic() -> None:
    left = runner()
    right = runner()
    left.enable("dirty")
    right.enable("dirty")

    assert left.tick(0) == right.tick(0)
    assert left.tick(1) == right.tick(1)
    assert left.active_names == ("baseline", "dirty")


def test_value_injectors_apply_to_native_ids_and_preserve_stuck_value() -> None:
    current = runner()
    current.enable("dirty")

    first = current.tick(1)
    second = current.tick(2)
    assert first["40101"] == second["40101"]
    assert first["40101"] < 0 or first["40101"] > 100
    assert current.tick(5)["40101"] != current.tick(1)["40101"]
    assert current.tick(5)["40101"] != current.tick(5)["40101"]  # NaN is never equal to itself


def test_metadata_and_transport_hooks_follow_time_window() -> None:
    current = runner()
    current.enable("dirty")
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    assert current.get_source_timestamp("LEVEL", timestamp, 1) == timestamp.replace(hour=1)
    assert current.get_opc_status("LEVEL", 1) != current.good_status
    assert current.filter_opc_nodes(["ns=2;s=LEVEL"], 1) == ["ns=2;s=LEVEL", "ns=2;s=NEW"]
    assert current.is_connection_drop_active("modbus_tcp", 1)
    assert current.should_corrupt_modbus_frame(1)
    assert not current.is_connection_drop_active("opcua", 1)
    assert not current.should_corrupt_modbus_frame(10)


def test_duplicate_delivery_returns_two_snapshots() -> None:
    current = runner()
    current.enable("dirty")

    deliveries = current.deliveries(1)
    assert len(deliveries) == 2
    assert deliveries[0] == deliveries[1]


def test_yaml_config_can_be_loaded(tmp_path: Path) -> None:
    yaml_path = tmp_path / "scenarios.yaml"
    yaml_path.write_text("scenarios:\n  - name: baseline\n    enabled: true\n    seed: 42\n    injectors: []\n", encoding="utf-8")

    current = ScenarioRunner(yaml_path, TagGenerator(seed=1, profile=PROFILE))
    assert current.active_names == ("baseline",)


def test_unknown_scenario_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown scenario"):
        runner().enable("missing")
