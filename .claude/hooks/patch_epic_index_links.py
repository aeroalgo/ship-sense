#!/usr/bin/env python3
"""Patch human index/link files: epic step shards sNN/eNN/rNN *.md → *.yaml."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

S_STEP = re.compile(r"(s\d{2}-[a-z0-9-]+)\.md", re.I)
R_IMPL = re.compile(
    r"(implement/implement-[^)\s]*?)(r\d{2}-[a-z0-9-]+)\.md", re.I
)
R_LOCAL = re.compile(r"(?<![/])(r\d{2}-[a-z0-9-]+)\.md", re.I)


def patch_text(text: str, *, allow_s: bool = True, allow_r_impl: bool = False, allow_r_local: bool = False) -> str:
    if allow_s:
        text = S_STEP.sub(r"\1.yaml", text)
    if allow_r_impl:
        text = R_IMPL.sub(r"\1\2.yaml", text)
    if allow_r_local:
        text = R_LOCAL.sub(r"\1.yaml", text)
    return text


def patch_file(path: Path, *, allow_s: bool = True, allow_r_impl: bool = False, allow_r_local: bool = False) -> bool:
    raw = path.read_text(encoding="utf-8")
    new = patch_text(raw, allow_s=allow_s, allow_r_impl=allow_r_impl, allow_r_local=allow_r_local)
    if new == raw:
        return False
    path.write_text(new, encoding="utf-8")
    print(f"→ {path.relative_to(ROOT)}")
    return True


def main() -> int:
    count = 0
    flags: dict[Path, dict[str, bool]] = {}

    def add(path: Path, **kw: bool) -> None:
        f = flags.setdefault(path, {"allow_s": False, "allow_r_impl": False, "allow_r_local": False})
        f.update(kw)

    for role in ("back", "front"):
        base = ROOT / "memory-bank" / role
        if not base.is_dir():
            continue
        for idx in base.glob("plan/decompose-*/index.md"):
            add(idx, allow_s=True)
        for idx in base.glob("implement/implement-*/index.md"):
            add(idx, allow_s=True)

    rf_dec = ROOT / "memory-bank/back/refactor/plan/decompose-rf-fastapi-template-ownership/index.md"
    rf_impl = ROOT / "memory-bank/back/refactor/implement/implement-rf-fastapi-template-ownership/index.md"
    if rf_dec.is_file():
        add(rf_dec, allow_r_impl=True)
    if rf_impl.is_file():
        add(rf_impl, allow_r_impl=True, allow_s=True, allow_r_local=True)

    for p in (
        ROOT / "memory-bank/tasks.md",
        ROOT / "memory-bank/back/bugfix/v1-p2-ship/bugfix-20260801-stop-gate-result-fixture.md",
    ):
        if p.is_file():
            add(p, allow_s=True)

    for path, f in flags.items():
        if patch_file(path, **f):
            count += 1

    print(f"patched {count} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
