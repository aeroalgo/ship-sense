from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, select

from app.warnings.schemas import DriftWarning, WarningHistoryResponse, WarningTransition


class WarningService:
    async def list_active(
        self,
        session: Any,
        *,
        active: bool | None,
        tag_id: str | None,
        asset_id: str | None,
        since: datetime | None,
    ) -> list[DriftWarning]:
        query = "SELECT * FROM warnings_active"
        conditions: list[str] = []
        values: dict[str, object] = {}
        if active is not None:
            conditions.append("status = :active_status")
            values["active_status"] = "active" if active else "cleared"
        if tag_id is not None:
            conditions.append("tag_id = :tag_id")
            values["tag_id"] = tag_id
        if asset_id is not None:
            conditions.append("asset_id = :asset_id")
            values["asset_id"] = asset_id
        if since is not None:
            conditions.append("since >= :since")
            values["since"] = since
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY since DESC, tag_id ASC"
        rows = await _execute_rows(session, query, values)
        return [DriftWarning.model_validate(dict(row)) for row in rows]

    async def history(
        self,
        session: Any,
        *,
        tag_id: str | None,
        asset_id: str | None,
        since: datetime | None,
        limit: int,
        offset: int,
    ) -> tuple[list[WarningTransition], bool]:
        query = "SELECT warning_json, from_status, to_status, occurred_at, tag_id FROM warnings_history"
        conditions: list[str] = []
        values: dict[str, object] = {"limit": limit + 1, "offset": offset}
        if tag_id is not None:
            conditions.append("tag_id = :tag_id")
            values["tag_id"] = tag_id
        if since is not None:
            conditions.append("occurred_at >= :since")
            values["since"] = since
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY occurred_at DESC, id DESC LIMIT :limit OFFSET :offset"
        rows = await _execute_rows(session, query, values)
        has_more = len(rows) > limit
        items = [WarningTransition.model_validate(dict(row["warning_json"])) for row in rows[:limit]]
        return items, has_more

    async def overlapping(self, session: Any, *, from_ts: datetime, to_ts: datetime) -> list[DriftWarning]:
        query = "SELECT warning_json FROM warnings_history WHERE occurred_at < :to_ts"
        rows = await _execute_rows(session, query, {"to_ts": to_ts})
        return [DriftWarning.model_validate(dict(row["warning_json"])) for row in rows]


async def _execute_rows(session: Any, query: str, params: dict[str, object]) -> list[Any]:
    if hasattr(session, "execute"):
        result = await session.execute(query, params)
        if hasattr(result, "mappings"):
            return list(result.mappings().all())
        if hasattr(result, "all"):
            return list(result.all())
    return []
