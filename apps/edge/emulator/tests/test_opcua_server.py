from __future__ import annotations

import asyncio

import pytest
from asyncua import Client, ua

from emulator.protocols.opcua_server import OpcUaServerAdapter
from emulator.tag_model import TagGenerator


@pytest.fixture
def generator() -> TagGenerator:
    return TagGenerator(
        seed=7,
        profile={
            "id": "test",
            "tick_hz": 20.0,
            "signals": [
                {
                    "signal_id": "RPM",
                    "native_ids": {"opcua": "ns=2;s=AI4104"},
                    "value_type": "float32",
                    "generator": {"kind": "constant", "value": 1800.0},
                },
                {
                    "signal_id": "COUNT",
                    "native_ids": {"opcua": "ns=2;s=STUB0001"},
                    "value_type": "int16",
                    "generator": {"kind": "constant", "value": 42},
                },
            ],
        },
    )


@pytest.mark.asyncio
async def test_server_browses_read_only_nodes_and_exposes_profile_node_ids(
    generator: TagGenerator,
) -> None:
    adapter = OpcUaServerAdapter(generator)
    await adapter.start(port=0)

    client = Client(adapter.endpoint)
    try:
        await client.connect()
        objects = client.get_objects_node()
        emulator = None
        for node in await objects.get_children():
            if (await node.read_browse_name()).Name == "Emulator":
                emulator = node
                break
        assert emulator is not None
        nodes = await emulator.get_children()
        node_ids = {node.nodeid.to_string() for node in nodes}

        assert node_ids == set(adapter.node_ids)
        rpm = client.get_node("ns=2;s=AI4104")
        assert await rpm.read_value() == pytest.approx(1800.0)
        assert ua.AccessLevel.CurrentWrite not in await rpm.get_access_level()
    finally:
        await client.disconnect()
        await adapter.stop()


@pytest.mark.asyncio
async def test_monitored_item_receives_snapshot_update(
    generator: TagGenerator,
) -> None:
    adapter = OpcUaServerAdapter(generator)
    await adapter.start(port=0)

    client = Client(adapter.endpoint)
    updates: list[float] = []

    class Handler:
        def datachange_notification(self, node, value, data):
            updates.append(float(value))

    try:
        await client.connect()
        node = client.get_node("ns=2;s=AI4104")
        subscription = await client.create_subscription(20, Handler())
        await subscription.subscribe_data_change(node)
        await asyncio.sleep(0.15)

        assert updates
        assert updates[-1] == pytest.approx(1800.0)
        await subscription.delete()
    finally:
        await client.disconnect()
        await adapter.stop()


@pytest.mark.asyncio
async def test_stop_is_idempotent_and_bind_requires_not_running(
    generator: TagGenerator,
) -> None:
    adapter = OpcUaServerAdapter()
    with pytest.raises(RuntimeError, match="TagGenerator is not bound"):
        await adapter.start(port=0)

    adapter.bind(generator)
    await adapter.start(port=0)
    with pytest.raises(RuntimeError, match="cannot bind"):
        adapter.bind(generator)
    await adapter.stop()
    await adapter.stop()
    assert not adapter.running
