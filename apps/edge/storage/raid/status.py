from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RaidSnapshot:
    pool: str
    state: str
    degraded: bool
    resilvering: bool
    health: str
    reason: str | None = None


class RaidHealth:
    ONLINE = "online"
    DEGRADED = "degraded"
    RESILVERING = "resilvering"
    UNKNOWN = "unknown"


def parse_zpool_status(output: str, *, pool: str = "shipsense") -> RaidSnapshot:
    try:
        payload: dict[str, Any] = json.loads(output)
        state = str(payload["state"]).upper()
        scan = payload.get("scan") or {}
        scan_state = str(scan.get("state", "")).lower()
    except (json.JSONDecodeError, TypeError, KeyError):
        return RaidSnapshot(pool, RaidHealth.UNKNOWN, True, False, RaidHealth.UNKNOWN, "invalid_output")

    if state == "ONLINE" and scan_state not in {"resilvering", "scrubbing"}:
        return RaidSnapshot(pool, state.lower(), False, False, RaidHealth.ONLINE)
    if scan_state == "resilvering":
        return RaidSnapshot(pool, state.lower(), True, True, RaidHealth.RESILVERING, "resilvering")
    if state == "DEGRADED":
        return RaidSnapshot(pool, state.lower(), True, False, RaidHealth.DEGRADED, "pool_degraded")
    return RaidSnapshot(pool, state.lower(), True, False, RaidHealth.UNKNOWN, "unknown_state")
