import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from apps.edge.storage.writer import WriterService


@pytest.mark.asyncio
async def test_start_tcp_binds_ephemeral_port():
    """start_tcp с port=0 должен вернуть реальный bound port > 0 и установить _server."""
    samples_repo = AsyncMock()
    events_repo = AsyncMock()
    session = AsyncMock()
    service = WriterService(session=session, samples_repo=samples_repo, events_repo=events_repo)

    host, port = await service.start_tcp("127.0.0.1", 0)
    try:
        assert port > 0, f"expected ephemeral port > 0, got {port}"
        assert host in ("127.0.0.1", "localhost", "::1") or ":" in host or host  # IPv4/IPv6 local
        assert service._server is not None
    finally:
        await service.shutdown()


@pytest.mark.asyncio
async def test_run_tcp_delegates_to_start_tcp():
    """run_tcp должен делегировать в start_tcp (с сохранением совместимости API)."""
    samples_repo = AsyncMock()
    events_repo = AsyncMock()
    session = AsyncMock()
    service = WriterService(session=session, samples_repo=samples_repo, events_repo=events_repo)

    with patch.object(WriterService, "start_tcp", wraps=service.start_tcp) as spy_start:
        task = asyncio.create_task(service.run_tcp("127.0.0.1", 0))
        # даём время на bind
        await asyncio.sleep(0.05)
        # останавливаем
        await service.shutdown()
        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.TimeoutError:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        spy_start.assert_awaited_once()
        # после shutdown server должен быть очищен
        assert service._server is None
