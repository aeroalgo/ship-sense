from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from collector.plugins.modbus.client import (
    AsyncModbusClient,
    ModbusClientError,
    ModbusTimeoutError,
)


# =============================================================================
# Fixtures and helpers
# =============================================================================


def _make_mock_client() -> MagicMock:
    """Создать mock AsyncModbusTcpClient с read_holding/read_input."""
    mock = MagicMock()
    mock.connect = AsyncMock(return_value=True)
    mock.close = MagicMock()
    mock.connected = True

    # read_holding_registers возвращает response с .registers и isError()=False
    mock_read_holding = AsyncMock()
    mock_read_holding_response = MagicMock()
    # 42.0 float32 ABCD
    mock_read_holding_response.registers = [0x4228, 0x0000]
    mock_read_holding_response.isError = MagicMock(return_value=False)
    mock_read_holding.return_value = mock_read_holding_response
    mock.read_holding_registers = mock_read_holding

    # read_input_registers
    mock_read_input = AsyncMock()
    mock_read_input_response = MagicMock()
    mock_read_input_response.registers = [0x0001, 0x0002]
    mock_read_input_response.isError = MagicMock(return_value=False)
    mock_read_input.return_value = mock_read_input_response
    mock.read_input_registers = mock_read_input

    return mock


# =============================================================================
# Конструктор и lifecycle (connect / disconnect)
# =============================================================================


def test_async_modbus_client_constructs() -> None:
    """Клиент конструируется с host/port/timeout."""
    client = AsyncModbusClient(host="127.0.0.1", port=502, timeout=1.5)
    assert client.host == "127.0.0.1"
    assert client.port == 502
    assert client.timeout == 1.5
    assert client.connected is False


@pytest.mark.asyncio
async def test_connect_success_sets_connected() -> None:
    """connect() → True → connected=True."""
    mock_pymodbus = _make_mock_client()

    with patch(
        "collector.plugins.modbus.client.AsyncModbusTcpClient",
        return_value=mock_pymodbus,
    ):
        client = AsyncModbusClient(host="127.0.0.1", port=1502)
        result = await client.connect()

        assert result is True
        assert client.connected is True
        mock_pymodbus.connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_connect_failure_returns_false() -> None:
    """connect() → False (TCP fail) → connected=False, не роняет."""
    mock_pymodbus = _make_mock_client()
    mock_pymodbus.connect = AsyncMock(return_value=False)

    with patch(
        "collector.plugins.modbus.client.AsyncModbusTcpClient",
        return_value=mock_pymodbus,
    ):
        client = AsyncModbusClient(host="127.0.0.1", port=1502)
        result = await client.connect()

        assert result is False
        assert client.connected is False


@pytest.mark.asyncio
async def test_disconnect_closes_and_resets_connected() -> None:
    """disconnect() вызывает close и сбрасывает connected."""
    mock_pymodbus = _make_mock_client()

    with patch(
        "collector.plugins.modbus.client.AsyncModbusTcpClient",
        return_value=mock_pymodbus,
    ):
        client = AsyncModbusClient(host="127.0.0.1", port=1502)
        await client.connect()
        assert client.connected is True

        await client.disconnect()

        assert client.connected is False
        mock_pymodbus.close.assert_called_once()


@pytest.mark.asyncio
async def test_reconnect_after_disconnect() -> None:
    """reconnect() после disconnect: повторный connect."""
    mock_pymodbus = _make_mock_client()

    with patch(
        "collector.plugins.modbus.client.AsyncModbusTcpClient",
        return_value=mock_pymodbus,
    ):
        client = AsyncModbusClient(host="127.0.0.1", port=1502)
        await client.connect()
        await client.disconnect()
        assert client.connected is False

        result = await client.reconnect()

        assert result is True
        assert client.connected is True
        # connect вызван дважды (первый + reconnect)
        assert mock_pymodbus.connect.await_count == 2


# =============================================================================
# Read holding (FC03)
# =============================================================================


@pytest.mark.asyncio
async def test_read_holding_success_returns_registers() -> None:
    """read_holding(40001, count=2) → [0x4228, 0x0000]."""
    mock_pymodbus = _make_mock_client()

    with patch(
        "collector.plugins.modbus.client.AsyncModbusTcpClient",
        return_value=mock_pymodbus,
    ):
        client = AsyncModbusClient(host="127.0.0.1", port=1502)
        await client.connect()

        regs = await client.read_holding(address=40001, count=2)

        assert regs == [0x4228, 0x0000]
        mock_pymodbus.read_holding_registers.assert_awaited_once_with(
            address=40001, count=2, device_id=1
        )


@pytest.mark.asyncio
async def test_read_holding_requires_connected() -> None:
    """read_holding до connect → ModbusClientError."""
    mock_pymodbus = _make_mock_client()

    with patch(
        "collector.plugins.modbus.client.AsyncModbusTcpClient",
        return_value=mock_pymodbus,
    ):
        client = AsyncModbusClient(host="127.0.0.1", port=1502)
        # не подключаемся

        with pytest.raises(ModbusClientError, match="not connected"):
            await client.read_holding(address=40001, count=1)


# =============================================================================
# Read input (FC04)
# =============================================================================


@pytest.mark.asyncio
async def test_read_input_success_returns_registers() -> None:
    """read_input(30001, count=2) → [0x0001, 0x0002]."""
    mock_pymodbus = _make_mock_client()

    with patch(
        "collector.plugins.modbus.client.AsyncModbusTcpClient",
        return_value=mock_pymodbus,
    ):
        client = AsyncModbusClient(host="127.0.0.1", port=1502)
        await client.connect()

        regs = await client.read_input(address=30001, count=2)

        assert regs == [0x0001, 0x0002]
        mock_pymodbus.read_input_registers.assert_awaited_once_with(
            address=30001, count=2, device_id=1
        )


# =============================================================================
# Timeout (AC-B2-09)
# =============================================================================


@pytest.mark.asyncio
async def test_read_holding_timeout_raises_typed_error() -> None:
    """Таймаут → ModbusTimeoutError (typed, не generic Exception)."""
    mock_pymodbus = _make_mock_client()
    mock_pymodbus.read_holding_registers = AsyncMock(
        side_effect=asyncio.TimeoutError("read timeout")
    )

    with patch(
        "collector.plugins.modbus.client.AsyncModbusTcpClient",
        return_value=mock_pymodbus,
    ):
        client = AsyncModbusClient(host="127.0.0.1", port=1502, timeout=0.1)
        await client.connect()

        with pytest.raises(ModbusTimeoutError, match="timed out"):
            await client.read_holding(address=40001, count=1)


# =============================================================================
# Exception propagation (AC-B2-08)
# =============================================================================


@pytest.mark.asyncio
async def test_modbus_exception_propagates_without_killing_loop() -> None:
    """Modbus exception на одном read.

    Исключение, но следующий read возможен.
    """
    from pymodbus.exceptions import ModbusException

    mock_pymodbus = _make_mock_client()

    # Первый read → exception, второй → успех
    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ModbusException("Illegal data address")
        resp = MagicMock()
        resp.registers = [0x1234]
        resp.isError = MagicMock(return_value=False)
        return resp

    mock_pymodbus.read_holding_registers = AsyncMock(side_effect=side_effect)

    with patch(
        "collector.plugins.modbus.client.AsyncModbusTcpClient",
        return_value=mock_pymodbus,
    ):
        client = AsyncModbusClient(host="127.0.0.1", port=1502)
        await client.connect()

        # Первый read падает
        with pytest.raises(ModbusException):
            await client.read_holding(address=40001, count=1)

        # Второй read успешен (цикл не убит)
        regs = await client.read_holding(address=40002, count=1)
        assert regs == [0x1234]


# =============================================================================
# Reconnect after disconnect (AC-B2-07)
# =============================================================================


@pytest.mark.asyncio
async def test_read_after_reconnect_uses_fresh_session() -> None:
    """reconnect → новый клиент; read использует его."""
    mock_pymodbus_1 = _make_mock_client()
    mock_pymodbus_2 = _make_mock_client()

    # Второй клиент возвращает другие данные
    mock_read_resp = MagicMock()
    mock_read_resp.registers = [0xFFFF]
    mock_read_resp.isError = MagicMock(return_value=False)
    mock_pymodbus_2.read_holding_registers = AsyncMock(
        return_value=mock_read_resp
    )

    call_idx = 0

    def client_factory(*args, **kwargs):
        nonlocal call_idx
        call_idx += 1
        return [mock_pymodbus_1, mock_pymodbus_2][call_idx - 1]

    with patch(
        "collector.plugins.modbus.client.AsyncModbusTcpClient",
        side_effect=client_factory,
    ):
        client = AsyncModbusClient(host="127.0.0.1", port=1502)
        await client.connect()
        await client.disconnect()
        await client.reconnect()

        regs = await client.read_holding(address=40001, count=1)

        assert regs == [0xFFFF]
        # read вызван на втором клиенте
        mock_pymodbus_2.read_holding_registers.assert_awaited_once()


# =============================================================================
# Static guard: no write FC exported (AC-B2-11)
# =============================================================================


def test_module_does_not_export_write_methods() -> None:
    """Публичный API клиента НЕ содержит write_* (FC05/06/15/16)."""
    from collector.plugins.modbus import client as client_module

    public_names = [n for n in dir(client_module) if not n.startswith("_")]
    write_names = [n for n in public_names if "write" in n.lower()]

    assert write_names == [], (
        f"Found write methods in public API: {write_names}"
    )


def test_async_modbus_client_instance_has_no_write_methods() -> None:
    """Экземпляр AsyncModbusClient не имеет write_* методов."""
    client = AsyncModbusClient(host="127.0.0.1")
    instance_methods = [
        m
        for m in dir(client)
        if not m.startswith("_") and callable(getattr(client, m))
    ]
    write_methods = [m for m in instance_methods if "write" in m.lower()]

    assert write_methods == [], (
        f"Found write methods on instance: {write_methods}"
    )


# =============================================================================
# Error types
# =============================================================================


def test_modbus_client_error_is_base() -> None:
    """ModbusClientError — базовый; Timeout — подкласс."""
    assert issubclass(ModbusTimeoutError, ModbusClientError)
    assert issubclass(ModbusClientError, Exception)


def test_modbus_timeout_error_message() -> None:
    """ModbusTimeoutError содержит контекст."""
    err = ModbusTimeoutError("read holding 40001 timed out after 1.5s")
    assert "40001" in str(err)
    assert "1.5s" in str(err)
