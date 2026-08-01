from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.health.schemas import (
    CheckStatus,
    HealthResponse,
    SourceStatus,
    SourcesStatusResponse,
)


_QUALITY_BY_STATE = {
    "up": "good",
    "reconnecting": "uncertain",
    "degraded": "uncertain",
    "down": "bad",
}


class HealthService:
    def __init__(self, *, snapshot_path: str | Path, version: str = "dev") -> None:
        self.snapshot_path = Path(snapshot_path)
        self.version = version
        self.started_at = time.monotonic()

    def _snapshot(self) -> dict[str, Any] | None:
        try:
            return json.loads(self.snapshot_path.read_text())
        except (OSError, TypeError, ValueError):
            return None

    async def build_health(self, session: Any, *, ws_connections: int = 0) -> HealthResponse:
        checks: dict[str, CheckStatus] = {}
        db_started = time.perf_counter()
        try:
            await session.execute(text("SELECT 1"))
        except (OSError, RuntimeError, ConnectionError, SQLAlchemyError):
            checks["db"] = CheckStatus(status="down")
        else:
            checks["db"] = CheckStatus(
                status="ok", latency_ms=(time.perf_counter() - db_started) * 1000
            )

        snapshot = self._snapshot()
        collector_ok = snapshot is not None and snapshot.get("collector_state") in {
            "running",
            "degraded",
        }
        checks["collector"] = CheckStatus(
            status="ok" if collector_ok else "stale",
            last_sample_ts=_snapshot_ts(snapshot),
        )
        checks["disk"] = CheckStatus(status="unknown", path="/")
        checks["ws"] = CheckStatus(status="ok", active_connections=ws_connections)
        return HealthResponse(
            status="ok" if checks["db"].status == "ok" else "degraded",
            version=self.version,
            uptime_sec=time.monotonic() - self.started_at,
            checks=checks,
        )

    def sources_status(self) -> SourcesStatusResponse:
        snapshot = self._snapshot() or {}
        items: list[SourceStatus] = []
        for source in snapshot.get("sources", []):
            state = str(source.get("state", "down"))
            source_id = str(source.get("source_id", "unknown"))
            items.append(
                SourceStatus(
                    source_id=source_id,
                    name=source_id,
                    connected=bool(source.get("connected", state == "up")),
                    last_poll_ts=_parse_ts(source.get("last_ok_ts")),
                    error_count_24h=int(source.get("reconnect_count", 0)),
                    quality_summary=_QUALITY_BY_STATE.get(state, "uncertain"),
                    tags_active=int(source.get("tags_active", 0)),
                    tags_quarantine=int(source.get("tags_quarantine", 0)),
                    tags_stale=int(source.get("tags_stale", 0)),
                )
            )
        return SourcesStatusResponse(items=items)


def _parse_ts(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _snapshot_ts(snapshot: dict[str, Any] | None) -> datetime | None:
    return _parse_ts(snapshot.get("ts")) if snapshot else None
