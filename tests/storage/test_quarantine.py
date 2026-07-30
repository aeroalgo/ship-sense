"""s15 — Quarantine diff + persist TDD (RED first).

Pure diff + async apply/ack against tag_quarantine.
Dual-path quality=4 verified via writer path.
Uses mocks (no real DB, per other storage tests).
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.telemetry.models import Quality, TelemetrySample
from app.semantic.models import NativeMap, NativeMapMapping, QuarantineEntry, QuarantineKind, QuarantineReport
from app.semantic.quarantine import (
    acknowledge,
    apply_quarantine,
    diff_native_map,
)
from apps.edge.storage.writer import WriterService


def _native_map(mappings: list[tuple[str, str]]) -> NativeMap:
    return NativeMap(
        version="live-1",
        approved=False,
        mappings=[NativeMapMapping(native_id=nid, tag_id=tid, codec="float32") for nid, tid in mappings],
    )


# --------------------------------------------------------------------------- #
# Pure diff (no side effects)
# --------------------------------------------------------------------------- #

def test_diff_native_map_added_for_unknown_native() -> None:
    approved = _native_map([("MODBUS:40001", "TAI4101")])
    new = _native_map([("MODBUS:40001", "TAI4101"), ("MODBUS:99999", "GHOST999")])
    report = diff_native_map(approved, new, known_tags={"TAI4101"})
    assert len(report.added) == 1
    e = report.added[0]
    assert e.kind == QuarantineKind.ADDED
    assert e.tag_id == "GHOST999"
    assert "native_unmapped" in e.reason or "native_to_unknown" in e.reason
    assert len(report.removed) == 0
    assert len(report.changed) == 0


def test_diff_native_map_changed_and_removed() -> None:
    approved = _native_map([("MODBUS:40001", "TAI4101"), ("MODBUS:40002", "TAI4102")])
    new = _native_map([("MODBUS:40001", "TAI4101"), ("MODBUS:40002", "TAI4201")])
    report = diff_native_map(approved, new, known_tags={"TAI4101", "TAI4102", "TAI4201"})
    # 40002 remapped -> changed
    assert len(report.changed) >= 1
    assert any("native_remap" in e.reason for e in report.changed)
    # no removed here
    # add a removal case
    new2 = _native_map([("MODBUS:40001", "TAI4101")])
    report2 = diff_native_map(approved, new2, known_tags={"TAI4101", "TAI4102"})
    assert len(report2.removed) >= 1
    assert any("native_removed" in e.reason for e in report2.removed)


def test_diff_native_map_no_change_when_identical() -> None:
    approved = _native_map([("MODBUS:40001", "TAI4101")])
    report = diff_native_map(approved, approved, known_tags={"TAI4101"})
    assert len(report.added) == 0
    assert len(report.removed) == 0
    assert len(report.changed) == 0


# --------------------------------------------------------------------------- #
# Persist apply + acknowledge
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_apply_quarantine_upserts_added_and_changed() -> None:
    session = AsyncMock()
    report = QuarantineReport(
        added=[
            QuarantineEntry(tag_id="T1", native_id="N1", reason="native_unmapped:N1", kind=QuarantineKind.ADDED),
        ],
        changed=[
            QuarantineEntry(tag_id="T2", native_id="N2", reason="native_remap:N2:old:new", kind=QuarantineKind.CHANGED),
        ],
    )
    await apply_quarantine(report, session)
    # at least one execute (insert on conflict)
    assert session.execute.await_count >= 1
    assert session.commit.await_count == 1


@pytest.mark.asyncio
async def test_acknowledge_sets_flag() -> None:
    session = AsyncMock()
    await acknowledge("T1", session)
    session.execute.assert_awaited_once()
    assert session.commit.await_count == 1
    stmt = session.execute.await_args.args[0]
    # best-effort: contains update acknowledged
    assert "acknowledged" in str(stmt).lower() or hasattr(stmt, "values")


# --------------------------------------------------------------------------- #
# Dual-path: writer forces quality=4 for quarantined tags (override 0-3, not bad)
# --------------------------------------------------------------------------- #

def _sample(tag_id: str, q: Quality = Quality.GOOD) -> TelemetrySample:
    now = datetime.now(timezone.utc)
    return TelemetrySample(
        tag_id=tag_id,
        value=42.0,
        unit="bar",
        source_ts=now,
        edge_ts=now,
        quality=q,
        source_id="test",
    )


@pytest.mark.asyncio
async def test_writer_forces_quality_quarantine_when_tag_quarantined() -> None:
    samples_repo = AsyncMock()
    events_repo = AsyncMock()
    session = AsyncMock()
    samples_repo.insert_batch.return_value = 1

    # engine with quarantined tag
    from app.semantic.engine import SemanticEngine
    eng = SemanticEngine()
    # seed directly for test (cache)
    eng._quarantined.add("TAI4101")  # type: ignore[attr-defined]

    service = WriterService(
        session=session,
        samples_repo=samples_repo,
        events_repo=events_repo,
        quarantined_tags=lambda: frozenset(eng.quarantined_tags),  # type: ignore[attr-defined]
    )

    s_good = _sample("TAI4101", Quality.GOOD)
    s_unc = _sample("TAI4101", Quality.UNCERTAIN)
    s_bad = _sample("TAI4101", Quality.BAD)

    await service.flush_batches([s_good, s_unc, s_bad])

    # the batch passed to repo should have forced QUARANTINE for non-bad
    batch = samples_repo.insert_batch.await_args.args[0]
    qualities = [b.quality for b in batch]
    # at least the good/unc should be forced to QUARANTINE
    assert Quality.QUARANTINE in qualities
    # bad remains bad (do not override)
    assert any(q == Quality.BAD for q in qualities)
