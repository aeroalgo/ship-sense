from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AccessAudit


class AccessAuditWriter:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, record: AccessAudit) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO access_audit
                    (ts, person_id, session_id, action, source_ip, details)
                VALUES
                    (:ts, :person_id, :session_id, :action, :source_ip, :details)
                """
            ),
            {
                "ts": record.ts,
                "person_id": record.person_id,
                "session_id": str(record.session_id) if record.session_id is not None else None,
                "action": record.action,
                "source_ip": record.source_ip,
                "details": json.dumps(record.details or {}),
            },
        )
        await self._session.commit()

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[AccessAudit]:
        bounded_limit = min(max(limit, 1), 1000)
        bounded_offset = max(offset, 0)
        result = await self._session.execute(
            text(
                """
                SELECT ts, person_id, session_id, action, host(source_ip) AS source_ip, details
                FROM access_audit
                ORDER BY ts DESC, id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"limit": bounded_limit, "offset": bounded_offset},
        )
        return [_to_record(row) for row in result.mappings().all()]


def _to_record(row: Mapping[str, Any]) -> AccessAudit:
    return AccessAudit(
        ts=row["ts"],
        person_id=row["person_id"],
        session_id=row["session_id"],
        action=row["action"],
        source_ip=row["source_ip"],
        details=row["details"] or {},
    )
