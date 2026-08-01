"""s20 T7 quarantine/stale acceptance matrix at the semantic boundary."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.semantic.engine import SemanticEngine
from app.semantic.loader import load_pack
from app.semantic.models import NativeMap, NativeMapMapping, TagDisplayState


PACK = Path(__file__).parents[2] / "fixtures" / "ship-pack-min"
UTC = timezone.utc
NOW = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)


TAG = "TAG_GOOD"
BASE_NATIVE = ("MODBUS:40001", TAG)


@pytest.fixture(autouse=True)
def _patch_pack_count(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.semantic import engine, loader

    monkeypatch.setattr(loader, "COUNT_TOLERANCE", 1)

    def load_pack_with_native_map(path):
        pack = load_pack(path)
        return pack.model_copy(
            update={
                "native_map": NativeMap(
                    version="approved-1",
                    approved=True,
                    mappings=[
                        NativeMapMapping(
                            native_id="MODBUS:40001",
                            tag_id=TAG,
                            codec="float32",
                        )
                    ],
                )
            }
        )

    monkeypatch.setattr(engine, "load_pack", load_pack_with_native_map)


def _engine() -> SemanticEngine:
    engine = SemanticEngine(now_provider=lambda: NOW)
    engine.load(PACK)
    return engine


def _native(*pairs: tuple[str, str]) -> NativeMap:
    return NativeMap(
        version="live-2",
        approved=False,
        mappings=[
            NativeMapMapping(native_id=native_id, tag_id=tag_id, codec="float32")
            for native_id, tag_id in pairs
        ],
    )


def test_added_mapping_is_quarantined_until_acknowledged() -> None:
    engine = _engine()
    report = engine.diff_native_map(_native(("MODBUS:40001", TAG), ("MODBUS:99999", TAG)))

    assert report.changed or report.added
    assert TAG in engine.quarantined_tags
    assert engine.get_tag_state(TAG) is TagDisplayState.QUARANTINE

    engine.acknowledge_quarantine(TAG)
    assert engine.get_tag_state(TAG) is TagDisplayState.NO_DATA


def test_removed_mapping_is_not_reported_as_valid_live_data() -> None:
    engine = _engine()
    report = engine.diff_native_map(_native(("MODBUS:40002", TAG)))

    assert report.removed or report.changed
    assert engine.get_tag_state(TAG) is TagDisplayState.QUARANTINE


def test_unresolvable_mapping_keeps_unknown_tag_out_of_quarantine_cache() -> None:
    engine = _engine()
    report = engine.diff_native_map(_native(("MODBUS:99999", "GHOST999")))

    assert any(entry.tag_id == "GHOST999" for entry in report.added)
    assert "GHOST999" not in engine.quarantined_tags
    assert engine.get_tag_state("GHOST999") is TagDisplayState.NO_DATA


def test_stale_tag_is_not_normal_after_expected_update_window() -> None:
    engine = _engine()
    engine.update_last_sample_ts("TAG_STALE", NOW - timedelta(seconds=100))

    assert engine.get_tag_state("TAG_STALE") is TagDisplayState.STALE
