"""Smoke test for pipeline DB E2E fixtures (T-002 s02).

AC-PIPE-01..05 infra: timescale + alembic + writer_tcp harness.
"""

import pytest
from sqlalchemy import text


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_timescale_alembic_ready(timescale_url: str, db_session) -> None:
    """После alembic upgrade head таблица samples существует и доступна."""
    # SELECT 1 — проверка подключения
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1

    # Таблица samples должна существовать после миграций
    result = await db_session.execute(
        text(
            "SELECT EXISTS ("
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'samples'"
            ")"
        )
    )
    assert result.scalar_one() is True
