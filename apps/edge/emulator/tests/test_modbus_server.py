from __future__ import annotations

from pathlib import Path

import pytest
from pymodbus.client import AsyncModbusTcpClient

from emulator.tag_model import TagGenerator, load_profile
from emulator.protocols.modbus_server import ModbusServerAdapter


TAGS_STUB = Path(__file__).resolve().parents[1] / "config" / "tags_stub.yaml"


@pytest.fixture
def generator() -> TagGenerator:
    return TagGenerator(
        seed=7,
        profile={
            "id": "test",
            "tick_hz": 1.0,
            "signals": [
                {
                    "signal_id": "RPM",
                    "native_ids": {"modbus": "40107"},
                    "value_type": "float32",
                    "generator": {"kind": "constant", "value": 1800.0},
                },
                {
                    "signal_id": "COUNT",
                    "native_ids": {"modbus": "41004"},
                    "value_type": "int16",
                    "generator": {"kind": "constant", "value": 42},
                },
            ],
        },
    )


@pytest.mark.asyncio
async def test_server_serves_holding_and_input_registers(
    generator: TagGenerator,
) -> None:
    adapter = ModbusServerAdapter()
    adapter.bind(generator)
    await adapter.start(host="127.0.0.1", port=0)

    client = AsyncModbusTcpClient("127.0.0.1", port=adapter.port)
    try:
        await client.connect()
        holding = await client.read_holding_registers(
            address=107,
            count=2,
            device_id=1,
        )
        input_registers = await client.read_input_registers(
            address=4,
            count=1,
            device_id=1,
        )

        assert not holding.isError()
        assert holding.registers == [0x44E1, 0x0000]
        assert not input_registers.isError()
        assert input_registers.registers == [42]
    finally:
        client.close()
        await adapter.stop()


@pytest.mark.asyncio
async def test_server_rejects_writes_and_stop_is_idempotent(
    generator: TagGenerator,
) -> None:
    adapter = ModbusServerAdapter()
    adapter.bind(generator)
    await adapter.start(host="127.0.0.1", port=0)

    client = AsyncModbusTcpClient("127.0.0.1", port=adapter.port)
    try:
        await client.connect()
        response = await client.write_register(
            address=1004,
            value=99,
            device_id=1,
        )
        assert response.isError()
    finally:
        client.close()
        await adapter.stop()
        await adapter.stop()
        assert not adapter.running


def test_build_context_accepts_full_tags_stub_profile() -> None:
    generator = TagGenerator(42, load_profile(TAGS_STUB))
    adapter = ModbusServerAdapter(generator)
    context = adapter._build_context(generator.tick(0))
    assert context.id == 1
    assert adapter._input_start == 4
    assert adapter._holding_start == 101


@pytest.mark.asyncio
async def test_server_starts_with_full_tags_stub_profile() -> None:
    generator = TagGenerator(42, load_profile(TAGS_STUB))
    adapter = ModbusServerAdapter(generator)
    await adapter.start(host="127.0.0.1", port=0)

    client = AsyncModbusTcpClient("127.0.0.1", port=adapter.port)
    try:
        await client.connect()
        holding = await client.read_holding_registers(
            address=107,
            count=2,
            device_id=1,
        )
        input_registers = await client.read_input_registers(
            address=4,
            count=2,
            device_id=1,
        )
        assert not holding.isError()
        assert not input_registers.isError()
        assert len(holding.registers) == 2
        assert len(input_registers.registers) == 2
    finally:
        client.close()
        await adapter.stop()
