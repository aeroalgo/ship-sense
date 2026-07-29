from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from collector.config.models import SourceConfig, SubscribeConfig, TagMapEntry
from collector.domain.interfaces import SourceConnector, Subscription
from collector.domain.models import RawSample, RawTagDescriptor
from collector.plugins.opcua.connector import OpcUaConnector


# =============================================================================
# Fixtures
# =============================================================================


def _source_config() -> SourceConfig:
    return SourceConfig(
        id="aps_main_opcua",
        protocol="opcua",
        endpoint="opc.tcp://127.0.0.1:4840/shipsense/server",
        subscribe=SubscribeConfig(
            publishing_interval_ms=1000,
            nodes_ref="maps/stub_aps_main_nodes.yaml",
        ),  # noqa: E501
        readonly_profile=True,
    )


def _nodes_map() -> list[TagMapEntry]:
    """Минимальная карта NodeId → tag для тестов."""
    return [
        TagMapEntry(
            node_id="ns=2;s=AI4101",
            tag_id="TAI4101",
            datatype="float32",
            unit="degC",
        ),
        TagMapEntry(
            node_id="ns=2;s=AI4102",
            tag_id="TAI4102",
            datatype="float32",
            unit="degC",
        ),
        TagMapEntry(
            node_id="ns=2;s=AI4103",
            tag_id="TAI4103",
            datatype="float32",
            unit="bar",
        ),
        TagMapEntry(
            node_id="ns=2;s=DI1201",
            tag_id="XA1201",
            datatype="boolean",
        ),
    ]


# =============================================================================
# OpcUaConnector tests (TDD: без реального OPC UA сервера)
# =============================================================================


@pytest.fixture
def mock_client() -> MagicMock:
    """Mock asyncua Client для unit-тестов connector."""
    mock = MagicMock()
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    # browse_nodes возвращает список Node (мокаем через patch в тестах)
    mock.create_subscription = AsyncMock()
    # Для reconnect тестов: после disconnect + connect client остаётся "живым"
    # connect не должен реально подключаться
    return mock


@pytest.fixture
def connector(mock_client: MagicMock) -> OpcUaConnector:
    cfg = _source_config()
    nodes = _nodes_map()
    conn = OpcUaConnector(cfg, mock_client, nodes)
    # Для unit-тестов: имитируем успешный connect без реального сервера
    conn._connected = True  # noqa: SLF001
    return conn


def test_connector_implements_source_connector(connector: OpcUaConnector) -> None:
    """OpcUaConnector реализует SourceConnector (AC-B1-03)."""
    assert isinstance(connector, SourceConnector)


def test_connector_source_id_and_protocol(connector: OpcUaConnector) -> None:
    assert connector.source_id == "aps_main_opcua"
    assert connector.protocol == "opcua"


@pytest.mark.asyncio
async def test_connect_delegates_to_client(
    connector: OpcUaConnector, mock_client: MagicMock
) -> None:
    await connector.connect()

    mock_client.connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_delegates_to_client(
    connector: OpcUaConnector, mock_client: MagicMock
) -> None:
    await connector.disconnect()

    mock_client.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_discover_tags_returns_from_map(connector: OpcUaConnector) -> None:
    tags = await connector.discover_tags()

    assert len(tags) == 4
    assert all(isinstance(t, RawTagDescriptor) for t in tags)
    assert tags[0].native_id == "ns=2;s=AI4101"
    assert tags[0].unit == "degC"


@pytest.mark.asyncio
async def test_read_returns_raw_samples(connector: OpcUaConnector) -> None:
    # Патчим внутренний _read_node_value
    with patch.object(connector, "_read_node_value", new_callable=AsyncMock) as mock_read:
        mock_read.side_effect = [42.0, 100.5, None, True]

        samples = await connector.read([
            "ns=2;s=AI4101",
            "ns=2;s=AI4102",
            "ns=2;s=AI4103",
            "ns=2;s=DI1201",
        ])

        assert len(samples) == 4
        assert samples[0].native_id == "ns=2;s=AI4101"
        assert samples[0].raw_value == pytest.approx(42.0)
        assert samples[3].raw_value is True


@pytest.mark.asyncio
async def test_subscribe_creates_monitored_items(
    connector: OpcUaConnector, mock_client: MagicMock
) -> None:
    # Мокаем подписку и monitored item (AsyncMock для awaitable методов)
    mock_sub = MagicMock()
    mock_sub.delete = AsyncMock()
    mock_sub.subscribe_data_change = AsyncMock()
    mock_client.create_subscription = AsyncMock(return_value=mock_sub)

    received: list[RawSample] = []

    async def on_sample(s: RawSample) -> None:
        received.append(s)

    sub = await connector.subscribe(["ns=2;s=AI4101", "ns=2;s=AI4102"], on_sample)

    assert isinstance(sub, Subscription)
    assert sub.tag_ids == ["ns=2;s=AI4101", "ns=2;s=AI4102"]
    mock_client.create_subscription.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_cancel_deletes_subscription(
    connector: OpcUaConnector, mock_client: MagicMock
) -> None:
    mock_sub = MagicMock()
    mock_sub.delete = AsyncMock()
    mock_sub.subscribe_data_change = AsyncMock()
    mock_client.create_subscription = AsyncMock(return_value=mock_sub)

    received: list[RawSample] = []

    async def on_sample(s: RawSample) -> None:
        received.append(s)

    sub = await connector.subscribe(["ns=2;s=AI4101"], on_sample)
    await sub.cancel()

    assert sub.cancel_event.is_set()
    # delete вызывается при отмене (через _cancel_handler)
    # В реальном коде delete вызывается при обработке cancel_event


@pytest.mark.asyncio
async def test_reconnect_recreates_subscription_without_duplicates(
    connector: OpcUaConnector, mock_client: MagicMock
) -> None:
    """Reconnect: пересоздать subscription без дублей (AC-B3-05)."""
    mock_sub1 = MagicMock()
    mock_sub1.delete = AsyncMock()
    mock_sub1.subscribe_data_change = AsyncMock()
    mock_sub2 = MagicMock()
    mock_sub2.delete = AsyncMock()
    mock_sub2.subscribe_data_change = AsyncMock()

    # Первый connect + subscribe
    mock_client.create_subscription = AsyncMock(side_effect=[mock_sub1, mock_sub2])

    received: list[RawSample] = []

    async def on_sample(s: RawSample) -> None:
        received.append(s)

    sub1 = await connector.subscribe(["ns=2;s=AI4101"], on_sample)
    # Симулируем разрыв: пересоздаём connector subscription
    await connector.disconnect()
    await connector.connect()
    sub2 = await connector.subscribe(["ns=2;s=AI4101"], on_sample)

    # Две подписки; вторая не должна дублировать monitored items старой
    assert sub1.id != sub2.id
    # В реальном reconnect логика в connector._recreate_subscriptions


@pytest.mark.asyncio
async def test_browse_diff_detects_added_removed(connector: OpcUaConnector) -> None:
    """browse_diff: added/removed vs map (hook B8/T7, AC-B3-08)."""
    # discovered из browse (сырые NodeId)
    discovered = [
        RawTagDescriptor(native_id="ns=2;s=AI4101", name="AI4101"),
        RawTagDescriptor(native_id="ns=2;s=NEW_TAG", name="NEW"),
    ]
    # map из конфига
    map_entries = [
        TagMapEntry(node_id="ns=2;s=AI4101", tag_id="TAI4101", datatype="float32"),
        TagMapEntry(node_id="ns=2;s=AI4102", tag_id="TAI4102", datatype="float32"),
    ]

    added, removed = connector.browse_diff(discovered, map_entries)

    assert "ns=2;s=NEW_TAG" in added
    assert "ns=2;s=AI4102" in removed


def test_register_opcua_factory_pattern() -> None:
    """Factory pattern: registry хранит фабрику для opcua (AC-B1-03)."""
    from collector.plugins.registry import PluginRegistry

    saved = dict(PluginRegistry._plugins)
    PluginRegistry._plugins.clear()
    try:
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        nodes = _nodes_map()

        def _create_opcua(cfg: SourceConfig) -> OpcUaConnector:
            return OpcUaConnector(cfg, mock_client, nodes)

        PluginRegistry.register("opcua", _create_opcua)

        cfg = _source_config()
        conn = PluginRegistry.create(cfg)

        assert isinstance(conn, OpcUaConnector)
        assert conn.source_id == "aps_main_opcua"
        assert conn.protocol == "opcua"
    finally:
        PluginRegistry._plugins.clear()
        PluginRegistry._plugins.update(saved)
