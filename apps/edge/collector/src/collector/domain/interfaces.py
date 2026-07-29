from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from collector.config.models import SourceConfig
from collector.domain.models import (
    Event,
    HealthStatus,
    RawSample,
    RawTagDescriptor,
    SourceState,
    TelemetrySample,
)


@dataclass(frozen=True)
class Subscription:
    """Ручка активной подписки плагина; cancel отменяет poll/monitored-items."""

    id: str
    tag_ids: list[str]
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)

    async def cancel(self) -> None:
        self.cancel_event.set()


OnSampleCallback = Callable[[RawSample], Awaitable[None]]


@runtime_checkable
class SourceConnector(Protocol):
    """
    Единый контракт плагина источника данных.

    Все методы async. Плагин не блокирует event loop синхронным I/O > 1ms.
    """

    @property
    def source_id(self) -> str: ...

    @property
    def protocol(self) -> str: ...

    async def connect(self) -> None:
        """Установить транспорт (TCP/TLS), подготовить session.

        Raises ConnectError при невозможности подключения.
        """

    async def discover_tags(self) -> list[RawTagDescriptor]:
        """Список тегов источника (Modbus: из карты; OPC UA: browse + merge)."""

    async def read(self, native_ids: list[str]) -> list[RawSample]:
        """Синхронное чтение набора native_id (каждый id → один RawSample)."""

    async def subscribe(
        self,
        native_ids: list[str],
        on_sample: OnSampleCallback,
    ) -> Subscription:
        """Push-режим. on_sample вызывается serially per connector instance."""

    async def healthcheck(self) -> HealthStatus:
        """Снимок состояния без side effects на соединение."""

    async def disconnect(self) -> None:
        """Idempotent. Закрыть сокеты/сессии, отменить subscribe tasks."""


class CanonicalSink(Protocol):
    """Получатель канонических данных (T-001): unit → IPC client к T-002 writer."""

    async def write_sample(self, sample: TelemetrySample) -> None: ...

    async def write_event(self, event: Event) -> None: ...


class BaseSourceConnector(ABC):
    """Optional base с общими helpers (metrics, recv_ts).

    Конкретные плагины (modbus_tcp, opcua) наследуются и реализуют abstractmethods.
    """

    def __init__(self, config: SourceConfig) -> None:
        self._config = config
        self._reconnect_count = 0
        self._last_ok_ts: datetime | None = None

    @property
    def source_id(self) -> str:
        return self._config.id

    @property
    def protocol(self) -> str:
        return self._config.protocol

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def discover_tags(self) -> list[RawTagDescriptor]: ...

    @abstractmethod
    async def read(self, native_ids: list[str]) -> list[RawSample]: ...

    @abstractmethod
    async def subscribe(
        self,
        native_ids: list[str],
        on_sample: OnSampleCallback,
    ) -> Subscription: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    async def healthcheck(self) -> HealthStatus:
        return HealthStatus(
            source_id=self.source_id,
            state=self._compute_state(),
            last_ok_ts=self._last_ok_ts,
            reconnect_count=self._reconnect_count,
        )

    def _compute_state(self) -> SourceState:
        """Default UP; плагин переопределяет по своему connection status."""
        return SourceState.UP

    def _recv_ts(self) -> datetime:
        """UTC-aware момент получения на edge (для RawSample.recv_ts)."""
        return datetime.now(timezone.utc)
