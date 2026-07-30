from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.telemetry.models import Quality, TelemetrySample
from apps.edge.storage.samples_repo import SamplesRepo


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1, 1.0), (1.5, 1.5), (True, 1.0), (None, None)],
)
@pytest.mark.asyncio
async def test_samples_repo_accepts_supported_numeric_payloads(value: object, expected: float | None) -> None:
    from unittest.mock import AsyncMock

    session = AsyncMock()
    repo = SamplesRepo(session)
    now = datetime.now(timezone.utc)
    sample = TelemetrySample(
        tag_id="TAG-1", value=value, unit="u", source_ts=now, edge_ts=now,
        quality=Quality.GOOD, source_id="test",
    )

    assert await repo.insert_batch([sample]) == 1
    statement = session.execute.await_args.args[0]
    assert expected in statement.compile().params.values()


@pytest.mark.asyncio
async def test_samples_repo_rejects_non_numeric_payload() -> None:
    from unittest.mock import AsyncMock

    now = datetime.now(timezone.utc)
    sample = TelemetrySample(
        tag_id="TAG-1", value="not numeric", unit="u", source_ts=now, edge_ts=now,
        quality=Quality.GOOD, source_id="test",
    )

    with pytest.raises(ValueError, match="numeric"):
        await SamplesRepo(AsyncMock()).insert_batch([sample])
