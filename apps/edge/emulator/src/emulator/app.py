from __future__ import annotations

import asyncio
from pathlib import Path

from emulator.dirt import ScenarioRunner
from emulator.protocols.modbus_server import ModbusServerAdapter
from emulator.protocols.opcua_server import OpcUaServerAdapter
from emulator.tag_model import TagGenerator, load_profile


class ScenarioGenerator:
    """Adapter exposing ScenarioRunner through the TagGenerator interface."""

    def __init__(self, runner: ScenarioRunner) -> None:
        self.runner = runner
        self.profile = runner.profile

    def tick(self, t: int) -> dict[str, object]:
        return self.runner.tick(t)

    @property
    def seed(self) -> int:
        return self.runner.generator.seed


async def run(
    profile_path: str | Path,
    scenarios_path: str | Path,
    seed: int = 42,
    host: str = "127.0.0.1",
    modbus_port: int = 502,
    opcua_port: int = 4840,
) -> None:
    profile = load_profile(profile_path)
    runner = ScenarioRunner(
        scenarios_path,
        TagGenerator(seed=seed, profile=profile),
    )
    generator = ScenarioGenerator(runner)
    modbus = ModbusServerAdapter(generator)
    opcua = OpcUaServerAdapter(generator)
    await modbus.start(host=host, port=modbus_port)
    await opcua.start(host=host, port=opcua_port)
    try:
        await asyncio.Event().wait()
    finally:
        await opcua.stop()
        await modbus.stop()
