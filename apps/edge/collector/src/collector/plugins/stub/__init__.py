"""AC-B1-08: demo third-party stub plugin package.

Import side-effect: регистрирует protocol ``stub`` в :class:`PluginRegistry`
без правки core registry кода. Импортируйте этот пакет (или модуль
``connector``), чтобы ``PluginRegistry.create(SourceConfig(protocol="stub"))``
вернул :class:`StubConnector`.
"""

from collector.plugins.registry import PluginRegistry
from collector.plugins.stub.connector import StubConnector

STUB_PROTOCOL = "stub"

PluginRegistry.register(STUB_PROTOCOL, StubConnector)

__all__ = ["STUB_PROTOCOL", "StubConnector"]
