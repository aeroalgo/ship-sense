"""Production collector entrypoint."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from collector.app import install_signal_handlers
from collector.runtime.bootstrap import runtime_from_environment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ShipSense edge collector")
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=Path("/var/lib/shipsense/health/collector.json"),
        help="Path to write health snapshot JSON",
    )
    parser.add_argument("--sources", type=Path, default=None)
    parser.add_argument("--maps-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    app = runtime_from_environment(
        snapshot_path=args.snapshot,
        sources_path=args.sources,
        maps_dir=args.maps_dir,
    )
    try:
        install_signal_handlers(app)
    except RuntimeError:
        pass

    try:
        await app.start()
        await app.run_until_stopped()
    finally:
        await app.stop()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))


__all__ = ["main"]
