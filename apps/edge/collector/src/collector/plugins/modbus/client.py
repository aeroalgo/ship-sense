from __future__ import annotations

import asyncio
from typing import Sequence

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

__all__ = [
    "AsyncModbusClient",
    "ModbusClientError",
    "ModbusTimeoutError",
]


class ModbusClientError(Exception):
    """Базовая ошибка клиента Modbus.

    Таймаут, отказ подключения, protocol error.
    """

    pass


class ModbusTimeoutError(ModbusClientError):
    """Таймаут запроса (AC-B2-09)."""

    pass


class AsyncModbusClient:
    """Async wrapper над pymodbus AsyncModbusTcpClient (FC03/04 only).

    Инвариант: публичный API НЕ экспортирует write_* (AC-B2-11).
    """

    def __init__(
        self,
        *,
        host: str,
        port: int = 502,
        timeout: float = 3.0,
        device_id: int = 1,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.device_id = device_id
        self._client: AsyncModbusTcpClient | None = None

    @property
    def connected(self) -> bool:
        """True если TCP-сессия активна."""
        return self._client is not None and self._client.connected

    async def connect(self) -> bool:
        """Установить TCP-соединение. Возвращает True/False (не роняет)."""
        if self._client is not None:
            # Уже есть клиент; если connected — ок, иначе переподключим
            if self._client.connected:
                return True
            # Закроем старый перед пересозданием
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

        self._client = AsyncModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
        )
        try:
            ok = await self._client.connect()
            if not ok:
                # connect() вернул False — не считаем подключенным
                self._client = None
                return False
            return True
        except Exception:
            # Любая ошибка подключения → False, не propagate
            self._client = None
            return False

    async def disconnect(self) -> None:
        """Закрыть сессию (идемпотентно)."""
        if self._client is not None:
            try:
                self._client.close()
            finally:
                self._client = None

    async def reconnect(self) -> bool:
        """Disconnect + connect. Для recovery после разрыва (AC-B2-07)."""
        await self.disconnect()
        return await self.connect()

    async def read_holding(
        self, *, address: int, count: int = 1
    ) -> Sequence[int]:
        """FC03: Read Holding Registers.

        Возвращает список регистров.

        Raises:
            ModbusClientError: если не connected.
            ModbusTimeoutError: таймаут (AC-B2-09).
            ModbusException: protocol exception (AC-B2-08).
                Пропагируется, не убивает цикл.
        """
        if not self.connected or self._client is None:
            raise ModbusClientError("not connected")

        try:
            resp = await asyncio.wait_for(
                self._client.read_holding_registers(
                    address=address, count=count, device_id=self.device_id
                ),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError as e:
            raise ModbusTimeoutError(
                f"read holding {address} timed out after {self.timeout}s"
            ) from e
        except ModbusException:
            # Protocol exception (illegal address, etc.) — propagate
            raise

        if getattr(resp, "isError", lambda: False)():
            # ExceptionResponse от сервера
            raise ModbusException(f"modbus exception: {resp}")

        return list(resp.registers)

    async def read_input(
        self, *, address: int, count: int = 1
    ) -> Sequence[int]:
        """FC04: Read Input Registers.

        Возвращает список регистров.
        """
        if not self.connected or self._client is None:
            raise ModbusClientError("not connected")

        try:
            resp = await asyncio.wait_for(
                self._client.read_input_registers(
                    address=address, count=count, device_id=self.device_id
                ),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError as e:
            raise ModbusTimeoutError(
                f"read input {address} timed out after {self.timeout}s"
            ) from e
        except ModbusException:
            raise

        if getattr(resp, "isError", lambda: False)():
            raise ModbusException(f"modbus exception: {resp}")

        return list(resp.registers)
