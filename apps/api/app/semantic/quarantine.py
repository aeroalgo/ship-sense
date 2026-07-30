"""Quarantine diff + persist (s15).

Pure diff of approved native_map vs live new_map.
Async apply/ack against tag_quarantine (PK=tag_id).
Engine cache refreshed by caller.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import delete, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.semantic.models import (
    NativeMap,
    QuarantineEntry,
    QuarantineKind,
    QuarantineReport,
)
from apps.edge.storage.schemas import TagQuarantine


# --------------------------------------------------------------------------- #
# Pure diff (no I/O, deterministic)
# --------------------------------------------------------------------------- #

def diff_native_map(
    approved: NativeMap | None,
    new_map: NativeMap,
    *,
    known_tags: set[str] | None = None,
) -> QuarantineReport:
    """Compute quarantine diff.

    Only tags that exist in approved pack assets produce quarantine rows.
    Unknown-tag entries are reported but skipped on apply.
    """
    known = known_tags or set()
    added: list[QuarantineEntry] = []
    removed: list[QuarantineEntry] = []
    changed: list[QuarantineEntry] = []

    if approved is None or not approved.mappings:
        # everything in new is candidate (but only known tags will be applied)
        for m in new_map.mappings:
            reason = f"native_unmapped:{m.native_id}"
            added.append(
                QuarantineEntry(
                    tag_id=m.tag_id,
                    native_id=m.native_id,
                    reason=reason,
                    kind=QuarantineKind.ADDED,
                )
            )
        return QuarantineReport(added=added, removed=removed, changed=changed)

    approved_map = {m.native_id: m.tag_id for m in approved.mappings}
    new_map_dict = {m.native_id: m.tag_id for m in new_map.mappings}

    # added / changed
    for nid, tag in new_map_dict.items():
        if nid not in approved_map:
            reason = (
                f"native_to_unknown_tag:{nid}:{tag}"
                if tag not in known
                else f"native_unmapped:{nid}"
            )
            added.append(
                QuarantineEntry(tag_id=tag, native_id=nid, reason=reason, kind=QuarantineKind.ADDED)
            )
        elif approved_map[nid] != tag:
            old = approved_map[nid]
            changed.append(
                QuarantineEntry(
                    tag_id=tag,
                    native_id=nid,
                    reason=f"native_remap:{nid}:{old}:{tag}",
                    kind=QuarantineKind.CHANGED,
                )
            )

    # removed
    for nid, tag in approved_map.items():
        if nid not in new_map_dict:
            removed.append(
                QuarantineEntry(tag_id=tag, native_id=nid, reason=f"native_removed:{nid}", kind=QuarantineKind.REMOVED)
            )

    return QuarantineReport(added=added, removed=removed, changed=changed)


# --------------------------------------------------------------------------- #
# Persist (full reconcile per diff)
# --------------------------------------------------------------------------- #

async def apply_quarantine(report: QuarantineReport, session: AsyncSession) -> None:
    """Upsert added+changed into tag_quarantine (acknowledged=false on insert or reason change).

    Delete removed rows (so they stop forcing quarantine state).
    Only apply for tags that are real (i.e. report already filtered or caller ensures).
    """
    # upsert added + changed
    to_upsert = list(report.added) + list(report.changed)
    if to_upsert:
        values = [
            {
                "tag_id": e.tag_id,
                "reason": e.reason,
                "native_id_hint": e.native_id,
                "acknowledged": False,
            }
            for e in to_upsert
        ]
        stmt = insert(TagQuarantine).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[TagQuarantine.tag_id],
            set_={
                "reason": stmt.excluded.reason,
                "native_id_hint": stmt.excluded.native_id_hint,
                "acknowledged": False,  # reset on new reason
                "since": text("now()"),
            },
        )
        await session.execute(stmt)

    # remove gone mappings
    if report.removed:
        tag_ids = [e.tag_id for e in report.removed]
        await session.execute(
            delete(TagQuarantine).where(TagQuarantine.tag_id.in_(tag_ids))
        )

    await session.commit()


async def acknowledge(tag_id: str, session: AsyncSession) -> None:
    """Mark a quarantine row as acknowledged=True. Idempotent."""
    stmt = (
        text("UPDATE tag_quarantine SET acknowledged = TRUE WHERE tag_id = :tid")
        .bindparams(tid=tag_id)
    )
    await session.execute(stmt)
    await session.commit()


async def refresh_quarantine_cache(session: AsyncSession, target_set: set[str]) -> None:
    """Load unacknowledged tag_ids from DB into caller's in-memory set (full replace)."""
    target_set.clear()
    rows = await session.execute(
        select(text("tag_id")).where(text("acknowledged = FALSE"))
    )
    for (tid,) in rows:
        if tid:
            target_set.add(tid)
