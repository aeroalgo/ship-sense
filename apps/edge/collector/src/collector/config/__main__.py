from __future__ import annotations

import argparse
import sys

from collector.config.loader import load_sources
from collector.config.validator import validate_config
from collector.domain.errors import ConfigError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m collector.config")
    parser.add_argument("command", choices=["validate"])
    args = parser.parse_args(argv)

    if args.command == "validate":
        try:
            sources = validate_config()
        except (ConfigError, FileNotFoundError, ValueError) as exc:
            print(f"config invalid: {exc}", file=sys.stderr)
            return 1
        print(f"config valid: {len(sources)} sources")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
