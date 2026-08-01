#!/usr/bin/env python3
"""Rewrite legacy integ-* schema lines → epic-* in memory-bank yaml shards."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "memory-bank"

REPLACEMENTS = (
    ("schema: integ-decompose/v1", "schema: epic-decompose/v1"),
    ("schema: integ-implement/v1", "schema: epic-implement/v1"),
)


def main() -> int:
    count = 0
    for path in sorted(ROOT.rglob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        new = text
        for old, new_val in REPLACEMENTS:
            new = new.replace(old, new_val)
        if new != text:
            path.write_text(new, encoding="utf-8")
            count += 1
            print(f"→ {path.relative_to(ROOT.parent)}")
    print(f"normalized {count} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
