from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Slot(StrEnum):
    A = "A"
    B = "B"


@dataclass(frozen=True, slots=True)
class RollbackDecision:
    target_slot: Slot
    should_rollback: bool


def rollback_after_failed_health(*, active_slot: Slot, pending_slot: Slot | None) -> RollbackDecision:
    if pending_slot is None or pending_slot == active_slot:
        return RollbackDecision(active_slot, False)
    return RollbackDecision(active_slot, True)


def resume_offset(*, downloaded_bytes: int, chunk_size: int) -> int:
    if downloaded_bytes < 0:
        raise ValueError("downloaded_bytes must not be negative")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    return downloaded_bytes - (downloaded_bytes % chunk_size)
