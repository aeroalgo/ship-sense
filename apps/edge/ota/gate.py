from __future__ import annotations

from enum import StrEnum


class AnchorageDecision(StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"


def can_update(*, anchored: bool | None, override: bool = False) -> AnchorageDecision:
    if override:
        return AnchorageDecision.ALLOWED
    return AnchorageDecision.ALLOWED if anchored is True else AnchorageDecision.BLOCKED
