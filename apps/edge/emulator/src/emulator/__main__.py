from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from emulator.app import run


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the ShipSense industrial emulator",
    )
    parser.add_argument(
        "--profile",
        default=str(Path(__file__).parents[3] / "config" / "tags_stub.yaml"),
    )
    parser.add_argument(
        "--scenarios",
        default=str(Path(__file__).parents[3] / "config" / "scenarios.yaml"),
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--modbus-port", type=int, default=502)
    parser.add_argument("--opcua-port", type=int, default=4840)
    args = parser.parse_args()
    asyncio.run(
        run(
            profile_path=args.profile,
            scenarios_path=args.scenarios,
            seed=args.seed,
            host=args.host,
            modbus_port=args.modbus_port,
            opcua_port=args.opcua_port,
        )
    )


if __name__ == "__main__":
    main()
