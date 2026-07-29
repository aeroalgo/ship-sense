from __future__ import annotations

from collections.abc import Callable

from collector.config.models import SourceConfig
from collector.domain.errors import ConfigError
from collector.domain.interfaces import SourceConnector

ConnectorSpec = (
    type[SourceConnector] | Callable[[SourceConfig], SourceConnector]
)


class PluginRegistry:
    """FR-B1-2: регистрация и фабрика плагинов источников.

    Class-level registry: `register("modbus_tcp", ModbusTcpConnector)` один раз
    при старте; `create(source_config)` — по `config.protocol`.
    """

    _plugins: dict[str, ConnectorSpec] = {}

    @classmethod
    def register(cls, protocol: str, connector_cls: ConnectorSpec) -> None:
        cls._plugins[protocol] = connector_cls

    @classmethod
    def create(cls, config: SourceConfig) -> SourceConnector:
        try:
            connector_cls = cls._plugins[config.protocol]
        except KeyError as exc:
            raise ConfigError(f"Unknown protocol: {config.protocol}") from exc
        return connector_cls(config)
