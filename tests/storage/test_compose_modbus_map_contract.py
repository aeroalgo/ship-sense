from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SOURCES_DEV = ROOT / "apps/edge/collector/config/sources.dev.yaml"
RUNTIME_MAP = ROOT / "apps/edge/collector/maps/stub_aps_main_runtime.yaml"
EMU_TAGS = ROOT / "apps/edge/emulator/config/tags_stub.yaml"


def test_dev_aps_main_map_is_subset_of_emulator_modbus_ids() -> None:
    sources = yaml.safe_load(SOURCES_DEV.read_text(encoding="utf-8"))
    aps = next(s for s in sources["sources"] if s["id"] == "aps_main")
    assert aps["tag_map_ref"] == "maps/stub_aps_main_runtime.yaml"

    coll = yaml.safe_load(RUNTIME_MAP.read_text(encoding="utf-8"))
    emu = yaml.safe_load(EMU_TAGS.read_text(encoding="utf-8"))
    emu_ids = {
        str(sig["native_ids"]["modbus"])
        for sig in emu["signals"]
        if sig.get("native_ids", {}).get("modbus")
    }
    for tag in coll["tags"]:
        base = str(tag["native_id"]).split(".", 1)[0]
        assert base in emu_ids, f"{tag['native_id']} missing on emulator stub"
