from unittest.mock import AsyncMock, Mock

import pytest

from apps.edge.storage.quota_manager import DiskUsage, QuotaManager, QuotaSettings


@pytest.mark.asyncio
async def test_check_and_degrade_alerts_at_eighty_percent_without_degrading():
    session = AsyncMock()
    manager = QuotaManager(session, settings=QuotaSettings(alert_pct=80, samples_quota_bytes=1000))
    manager._disk_usage = AsyncMock(return_value=DiskUsage(total_bytes=1000, used_bytes=810, postgres_bytes=0))
    manager._samples_size = AsyncMock(return_value=500)

    result = await manager.check_and_degrade()

    assert result.alerted is True
    assert result.degraded_chunks == 0
    assert result.bytes_freed == 0
    assert any("disk_80" in str(call.args) for call in session.execute.await_args_list)


@pytest.mark.asyncio
async def test_degrade_drops_oldest_samples_chunks_and_updates_watermark():
    session = AsyncMock()
    manager = QuotaManager(session, settings=QuotaSettings(alert_pct=80, samples_quota_bytes=100))
    manager._disk_usage = AsyncMock(return_value=DiskUsage(total_bytes=1000, used_bytes=100, postgres_bytes=0))
    manager._samples_size = AsyncMock(return_value=250)
    manager._oldest_chunks = AsyncMock(return_value=[("_hyper_1_1_chunk", 100), ("_hyper_1_2_chunk", 150)])
    manager._drop_chunk = AsyncMock()

    result = await manager.check_and_degrade()

    assert result.alerted is False
    assert result.degraded_chunks == 2
    assert result.bytes_freed == 250
    manager._drop_chunk.assert_any_await("_hyper_1_1_chunk")
    manager._drop_chunk.assert_any_await("_hyper_1_2_chunk")
    sql = " ".join(str(call.args[0]) for call in session.execute.await_args_list)
    assert "samples_degrade_log" in sql
    assert "samples_degrade_watermark" in sql
    assert "events" not in sql.lower()
