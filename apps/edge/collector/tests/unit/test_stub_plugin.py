from __future__ import annotations

import asyncio
from datetime import timezone

import pytest

from collector.config.models import SourceConfig
from collector.domain.interfaces import BaseSourceConnector, SourceConnector
from collector.domain.models import RawSample
from collector.plugins.registry import PluginRegistry

# AC-B1-08: demo third-party stub plugin — регистрируется импортом,
# без правки core registry.py (только register call в __init__).
import collector.plugins.stub  # noqa: F401  (import side-effect registration)


STUB_PROTOCOL = "stub"


@pytest.fixture
def stub_source() -> SourceConfig:
    return SourceConfig(id="stub_demo", protocol=STUB_PROTOCOL, endpoint="stub://internal")


def _create(source: SourceConfig) -> SourceConnector:
    return PluginRegistry.create(source)


def test_stub_protocol_registered_on_import(stub_source: SourceConfig) -> None:
    """Импорт collector.plugins.stub регистрирует protocol 'stub'."""
    connector = _create(stub_source)

    assert connector.protocol == STUB_PROTOCOL
    assert connector.source_id == "stub_demo"


def test_stub_connector_satisfies_protocol(stub_source: SourceConfig) -> None:
    connector = _create(stub_source)

    assert isinstance(connector, SourceConnector)
    assert isinstance(connector, BaseSourceConnector)


def test_stub_connect_and_read_yields_synthetic_samples(stub_source: SourceConfig) -> None:
    """Stub генерирует синтетику: каждый native_id → один RawSample."""
    connector = _create(stub_source)

    async def scenario() -> list[RawSample]:
        await connector.connect()
        try:
            return await connector.read(["ai4101", "di0101"])
        finally:
            await connector.disconnect()

    samples = asyncio.run(scenario())

    assert [s.native_id for s in samples] == ["ai4101", "di0101"]
    assert all(s.source_id == "stub_demo" for s in samples)
    assert all(s.recv_ts.tzinfo is not None for s in samples)


def test_stub_subscribe_pushes_synthetic_samples(stub_source: SourceConfig) -> None:
    """Push-режим: on_sample вызывается для каждого запрошенного native_id."""
    connector = _create(stub_source)
    received: list[RawSample] = []

    async def on_sample(sample: RawSample) -> None:
        received.append(sample)

    async def scenario() -> None:
        await connector.connect()
        subscription = await connector.subscribe(["ai4101"], on_sample)
        try:
            await subscription.cancel_event.wait()
        finally:
            await subscription.cancel()
            await connector.disconnect()

    asyncio.run(asyncio.wait_for(scenario(), timeout=2.0))

    assert [s.native_id for s in received] == ["ai4101"]
    assert all(isinstance(s, RawSample) for s in received)


def test_stub_discover_tags_returns_descriptors(stub_source: SourceConfig) -> None:
    connector = _create(stub_source)

    descriptors = asyncio.run(connector.discover_tags())

    assert descriptors
    assert all(d.native_id for d in descriptors)


def test_stub_healthcheck_is_up(stub_source: SourceConfig) -> None:
    connector = _create(stub_source)

    health = asyncio.run(connector.healthcheck())

    assert health.source_id == "stub_demo"
    assert health.state.value == "up"


def test_stub_disconnect_is_idempotent(stub_source: SourceConfig) -> None:
    connector = _create(stub_source)

    async def double_disconnect() -> None:
        await connector.connect()
        await connector.disconnect()
        await connector.disconnect()

    asyncio.run(asyncio.wait_for(double_disconnect(), timeout=2.0))


def test_stub_read_recv_ts_is_aware_utc(stub_source: SourceConfig) -> None:
    connector = _create(stub_source)

    sample = asyncio.run(connector.read(["ai4101"]))[0]

    assert sample.recv_ts.tzinfo is timezone.utc or sample.recv_ts.utcoffset() is not None
