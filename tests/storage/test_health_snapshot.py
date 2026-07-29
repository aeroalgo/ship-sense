from unittest.mock import AsyncMock, Mock, patch

import pytest

from apps.edge.storage.health import HealthSnapshotService


@pytest.mark.asyncio
async def test_snapshot_once_collects_metrics_persists_and_logs():
    session = AsyncMock()
    service = HealthSnapshotService(session, logger=Mock())
    usage = Mock(total=100 * 1024**3, used=81 * 1024**3, percent=81.0)
    memory = Mock(percent=42.5)
    result = Mock()
    result.scalar_one.side_effect = [2_000_000, 500_000]
    session.execute.return_value = result

    with patch("apps.edge.storage.health.psutil.disk_usage", return_value=usage), patch(
        "apps.edge.storage.health.psutil.virtual_memory", return_value=memory
    ), patch("apps.edge.storage.health.psutil.cpu_percent", return_value=12.5):
        row = await service.snapshot_once(queue_depth=7, extra={"writer_last_flush_ms": 8})

    assert row.disk_pct == 81.0
    assert row.ram_pct == 42.5
    assert row.cpu_pct == 12.5
    assert row.queue_depth == 7
    assert row.samples_bytes == 2_000_000
    assert row.events_bytes == 500_000
    assert row.extra == {"writer_last_flush_ms": 8, "alert": "disk_80"}
    sql = " ".join(str(call.args[0]) for call in session.execute.await_args_list)
    assert "health_snapshots" in sql
    service.logger.info.assert_called_once()
    assert service.logger.info.call_args.args[0] == "storage.health.snapshot"


@pytest.mark.asyncio
async def test_start_runs_periodic_snapshot_and_stop_cancels_task():
    service = HealthSnapshotService(AsyncMock(), interval_seconds=60)
    service.snapshot_once = AsyncMock()

    await service.start()
    await __import__("asyncio").sleep(0)
    await service.stop()

    service.snapshot_once.assert_awaited_once_with()
    assert service._task is None
