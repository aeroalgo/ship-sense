from __future__ import annotations

import asyncio
import collections.abc
import typing
from datetime import datetime, timezone

import pytest

from collector.config.models import SourceConfig
from collector.domain.errors import ConfigError
from collector.domain.interfaces import (
    BaseSourceConnector,
    CanonicalSink,
    OnSampleCallback,
    SourceConnector,
    Subscription,
)
from collector.domain.raw_models import RawSample, RawTagDescriptor
from collector.domain.health_models import SourceState
from collector.plugins.registry import PluginRegistry


class _FakeConnector(BaseSourceConnector):
    """Минимальный конкретный коннектор, покрывающий контракт SourceConnector."""

    async def connect(self) -> None: ...

    async def discover_tags(self) -> list[RawTagDescriptor]:
        return []

    async def read(self, native_ids: list[str]) -> list[RawSample]:
        return []

    async def subscribe(
        self,
        native_ids: list[str],
        on_sample: OnSampleCallback,
    ) -> Subscription:
        return Subscription(
            id="sub-1",
            tag_ids=list(native_ids),
            cancel_event=asyncio.Event(),
        )

    async def disconnect(self) -> None: ...

    def _compute_state(self) -> SourceState:
        return SourceState.UP


@pytest.fixture
def registry() -> type[PluginRegistry]:
    saved = dict(PluginRegistry._plugins)
    PluginRegistry._plugins.clear()
    yield PluginRegistry
    PluginRegistry._plugins.clear()
    PluginRegistry._plugins.update(saved)


def _source(protocol: str) -> SourceConfig:
    return SourceConfig(id="aps_main", protocol=protocol, endpoint="tcp://10.0.0.1:502")


def test_source_connector_protocol_is_runtime_checkable() -> None:
    assert isinstance(_FakeConnector(_source("modbus_tcp")), SourceConnector)


def test_register_and_create_modbus_tcp(registry: type[PluginRegistry]) -> None:
    registry.register("modbus_tcp", _FakeConnector)

    connector = registry.create(_source("modbus_tcp"))

    assert isinstance(connector, SourceConnector)
    assert connector.source_id == "aps_main"
    assert connector.protocol == "modbus_tcp"


def test_register_and_create_opcua(registry: type[PluginRegistry]) -> None:
    registry.register("opcua", _FakeConnector)

    connector = registry.create(_source("opcua"))

    assert isinstance(connector, SourceConnector)
    assert connector.protocol == "opcua"


def test_create_unknown_protocol_raises_config_error(registry: type[PluginRegistry]) -> None:
    with pytest.raises(ConfigError):
        registry.create(_source("canbus"))


def test_registry_stays_usable_after_unknown_protocol(registry: type[PluginRegistry]) -> None:
    with pytest.raises(ConfigError):
        registry.create(_source("canbus"))

    registry.register("modbus_tcp", _FakeConnector)
    assert isinstance(registry.create(_source("modbus_tcp")), SourceConnector)


def test_base_connector_healthcheck_returns_status() -> None:
    connector = _FakeConnector(_source("modbus_tcp"))

    health = asyncio.run(connector.healthcheck())

    assert health.source_id == "aps_main"
    assert health.state is SourceState.UP
    assert health.reconnect_count == 0


def test_subscription_cancel_sets_event() -> None:
    event = asyncio.Event()
    subscription = Subscription(id="s", tag_ids=["40101"], cancel_event=event)

    asyncio.run(subscription.cancel())

    assert event.is_set()


def test_subscription_is_frozen() -> None:
    subscription = Subscription(id="s", tag_ids=[], cancel_event=asyncio.Event())

    with pytest.raises(Exception):
        subscription.id = "x"  # type: ignore[misc]


def test_canonical_sink_is_a_protocol() -> None:
    assert issubclass(CanonicalSink, typing.Protocol)


def test_on_sample_callback_alias_is_callable_shape() -> None:
    assert typing.get_origin(OnSampleCallback) is collections.abc.Callable


def test_recv_ts_helper_is_aware_utc() -> None:
    connector = _FakeConnector(_source("modbus_tcp"))

    recv_ts = connector._recv_ts()

    assert recv_ts.tzinfo is not None
    assert recv_ts <= datetime.now(timezone.utc)
