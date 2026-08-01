"""Pure computed mnemo bindings."""
from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ComputedResult:
    value: float | None
    status: str
    excluded: tuple[str, ...] = ()


def sibling_mean_delta(
    target: Any,
    siblings: Mapping[str, Any],
    *,
    quarantined: frozenset[str] = frozenset(),
) -> ComputedResult:
    """Return target minus trusted sibling mean, or unknown without zero fallback."""
    excluded: list[str] = []
    if not _finite_number(target):
        return ComputedResult(None, "unknown", ("target",))
    trusted: list[float] = []
    for tag_id, value in siblings.items():
        if tag_id in quarantined or not _finite_number(value):
            excluded.append(tag_id)
            continue
        trusted.append(float(value))
    if not trusted:
        return ComputedResult(None, "unknown", tuple(excluded))
    return ComputedResult(float(target) - sum(trusted) / len(trusted), "ok", tuple(excluded))


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
