from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.audit.models import AccessAudit
from app.audit.writer import AccessAuditWriter


@pytest.mark.asyncio
async def test_access_audit_writer_appends_login_row() -> None:
    session = AsyncMock()
    record = AccessAudit(
        ts=datetime(2026, 7, 31, tzinfo=timezone.utc),
        person_id="ivanov",
        session_id=uuid4(),
        action="login",
        source_ip="192.0.2.10",
        details={"client": "test"},
    )

    await AccessAuditWriter(session).append(record)

    statement, params = session.execute.await_args.args
    assert "INSERT INTO access_audit" in str(statement)
    assert params["person_id"] == "ivanov"
    assert params["session_id"] == str(record.session_id)
    assert params["action"] == "login"
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_access_audit_writer_reads_paginated_rows() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.mappings.return_value.all.return_value = [
        {
            "ts": datetime(2026, 7, 31, tzinfo=timezone.utc),
            "person_id": "ivanov",
            "session_id": "00000000-0000-0000-0000-000000000001",
            "action": "logout",
            "source_ip": None,
            "details": {"reason": "logout"},
        }
    ]
    session.execute.return_value = result

    rows = await AccessAuditWriter(session).list(limit=10, offset=0)

    assert rows[0].person_id == "ivanov"
    assert rows[0].action == "logout"
    assert session.execute.await_args.args[1] == {"limit": 10, "offset": 0}
