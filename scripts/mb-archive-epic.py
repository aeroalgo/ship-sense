#!/usr/bin/env python3
"""Optional helper: move epic memory-bank artifacts into memory-bank/archive/{role}/ and rewrite external links.

User-facing entry: BACK|FRONT|INTEG ARCHIVE NOW (agent runs the workflow).
This script is optional — agent may call it for move+rewrite accuracy.

Usage (from repo root, usually by agent):
  python3 scripts/mb-archive-epic.py --role back --epic v1-p1-pipeline-db-e2e
  python3 scripts/mb-archive-epic.py --role back --epic v1-p1-pipeline-db-e2e --dry-run

Does NOT move reflection/. Rewrites tasks.md, tasks/log, reflection, activeContext,
and other markdown under memory-bank/ that still point at live role paths for this epic.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROLES = ("back", "front", "integration")
MOVE_MODES = ("plan", "implement", "creative", "qa", "bugfix")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def collect_sources(role_root: Path, epic: str) -> list[tuple[Path, Path]]:
    """Return list of (src, rel_under_role) to move."""
    items: list[tuple[Path, Path]] = []

    plan_file = role_root / "plan" / f"plan-{epic}.md"
    if plan_file.is_file():
        items.append((plan_file, Path("plan") / plan_file.name))

    decompose = role_root / "plan" / f"decompose-{epic}"
    if decompose.is_dir():
        items.append((decompose, Path("plan") / f"decompose-{epic}"))

    implement = role_root / "implement" / f"implement-{epic}"
    if implement.is_dir():
        items.append((implement, Path("implement") / f"implement-{epic}"))

    for mode in ("creative", "qa", "bugfix"):
        epic_dir = role_root / mode / epic
        if epic_dir.is_dir():
            items.append((epic_dir, Path(mode) / epic))

    # Legacy flat files containing epic slug
    for mode in ("qa", "bugfix", "creative"):
        mode_dir = role_root / mode
        if not mode_dir.is_dir():
            continue
        for p in mode_dir.iterdir():
            if p.name == epic:
                continue
            if p.is_file() and epic in p.name:
                items.append((p, Path(mode) / epic / p.name))
            elif p.is_dir() and epic in p.name and p.name != epic:
                items.append((p, Path(mode) / epic / p.name))

    # Dedupe by src
    seen: set[Path] = set()
    out: list[tuple[Path, Path]] = []
    for src, rel in items:
        src = src.resolve()
        if src in seen:
            continue
        seen.add(src)
        out.append((src, rel))
    return out


def move_tree(src: Path, dst: Path, dry_run: bool) -> None:
    if dst.exists():
        raise SystemExit(f"destination exists: {dst}")
    print(f"MOVE {src} -> {dst}")
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))


def rewrite_text(text: str, role: str, epic: str) -> str:
    """Rewrite live role paths → archive/role for this epic."""
    # Absolute-from-memory-bank style
    patterns = [
        (
            rf"(memory-bank/{role}/plan/plan-{re.escape(epic)}\.md)",
            rf"memory-bank/archive/{role}/plan/plan-{epic}.md",
        ),
        (
            rf"(memory-bank/{role}/plan/decompose-{re.escape(epic)})",
            rf"memory-bank/archive/{role}/plan/decompose-{epic}",
        ),
        (
            rf"(memory-bank/{role}/implement/implement-{re.escape(epic)})",
            rf"memory-bank/archive/{role}/implement/implement-{epic}",
        ),
        (
            rf"(memory-bank/{role}/creative/{re.escape(epic)})",
            rf"memory-bank/archive/{role}/creative/{epic}",
        ),
        (
            rf"(memory-bank/{role}/qa/{re.escape(epic)})",
            rf"memory-bank/archive/{role}/qa/{epic}",
        ),
        (
            rf"(memory-bank/{role}/bugfix/{re.escape(epic)})",
            rf"memory-bank/archive/{role}/bugfix/{epic}",
        ),
        # Legacy flat qa/bugfix/creative with epic in filename
        (
            rf"(memory-bank/{role}/qa/)(qa-[^)\s`]*{re.escape(epic)}[^)\s`]*)",
            rf"memory-bank/archive/{role}/qa/{epic}/\2",
        ),
        (
            rf"(memory-bank/{role}/bugfix/)(bugfix-[^)\s`]*{re.escape(epic)}[^)\s`]*)",
            rf"memory-bank/archive/{role}/bugfix/{epic}/\2",
        ),
        # Relative from role root (back/qa/...)
        (
            rf"(?<!archive/)({role}/plan/plan-{re.escape(epic)}\.md)",
            rf"archive/{role}/plan/plan-{epic}.md",
        ),
        (
            rf"(?<!archive/)({role}/plan/decompose-{re.escape(epic)})",
            rf"archive/{role}/plan/decompose-{epic}",
        ),
        (
            rf"(?<!archive/)({role}/implement/implement-{re.escape(epic)})",
            rf"archive/{role}/implement/implement-{epic}",
        ),
        (
            rf"(?<!archive/)({role}/qa/)(qa-[^)\s`]*{re.escape(epic)}[^)\s`]*)",
            rf"archive/{role}/qa/{epic}/\2",
        ),
        (
            rf"(?<!archive/)({role}/bugfix/)(bugfix-[^)\s`]*{re.escape(epic)}[^)\s`]*)",
            rf"archive/{role}/bugfix/{epic}/\2",
        ),
        (
            rf"(?<!archive/)({role}/creative/{re.escape(epic)})",
            rf"archive/{role}/creative/{epic}",
        ),
        (
            rf"(?<!archive/)({role}/qa/{re.escape(epic)})",
            rf"archive/{role}/qa/{epic}",
        ),
        (
            rf"(?<!archive/)({role}/bugfix/{re.escape(epic)})",
            rf"archive/{role}/bugfix/{epic}",
        ),
        # Relative from reflection/ (../qa|bugfix|creative|plan|implement)
        (
            rf"(\.\./qa/{re.escape(epic)})",
            rf"../../archive/{role}/qa/{epic}",
        ),
        (
            rf"(\.\./bugfix/{re.escape(epic)})",
            rf"../../archive/{role}/bugfix/{epic}",
        ),
        (
            rf"(\.\./creative/{re.escape(epic)})",
            rf"../../archive/{role}/creative/{epic}",
        ),
        (
            rf"(\.\./qa/)(qa-[^)\s`]*{re.escape(epic)}[^)\s`]*)",
            rf"../../archive/{role}/qa/{epic}/\2",
        ),
        (
            rf"(\.\./bugfix/)(bugfix-[^)\s`]*{re.escape(epic)}[^)\s`]*)",
            rf"../../archive/{role}/bugfix/{epic}/\2",
        ),
        (
            rf"(\.\./plan/plan-{re.escape(epic)}\.md)",
            rf"../../archive/{role}/plan/plan-{epic}.md",
        ),
        (
            rf"(\.\./plan/decompose-{re.escape(epic)})",
            rf"../../archive/{role}/plan/decompose-{epic}",
        ),
        (
            rf"(\.\./implement/implement-{re.escape(epic)})",
            rf"../../archive/{role}/implement/implement-{epic}",
        ),
    ]
    out = text
    for pat, repl in patterns:
        out = re.sub(pat, repl, out)
    return out


def rewrite_file(path: Path, role: str, epic: str, dry_run: bool) -> bool:
    if not path.is_file() or path.suffix not in {".md", ".mdc"}:
        return False
    # Skip files already under archive for this move target (internal relatives ok)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    new = rewrite_text(text, role, epic)
    if new == text:
        return False
    print(f"REWRITE {path}")
    if not dry_run:
        path.write_text(new, encoding="utf-8")
    return True


def iter_rewrite_targets(mb: Path, role: str, archive_role: Path) -> list[Path]:
    targets: list[Path] = []
    for name in ("tasks.md", "activeContext.md"):
        p = mb / name
        if p.is_file():
            targets.append(p)
    log_dir = mb / "tasks" / "log"
    if log_dir.is_dir():
        targets.extend(sorted(log_dir.glob("*.md")))
    reflection = mb / role / "reflection"
    if reflection.is_dir():
        targets.extend(sorted(reflection.rglob("*.md")))
    # Other live docs under role (van, task, …) — not archive, not sources being moved
    role_root = mb / role
    if role_root.is_dir():
        for p in role_root.rglob("*.md"):
            if archive_role in p.parents or archive_role == p:
                continue
            # skip trees we already moved (gone) — remaining
            if "reflection" in p.parts:
                continue  # already added
            targets.append(p)
    # Dedup
    seen: set[Path] = set()
    out: list[Path] = []
    for p in targets:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", required=True, choices=ROLES)
    ap.add_argument("--epic", required=True, help="plan_id / epic_id slug")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = repo_root()
    mb = root / "memory-bank"
    role_root = mb / args.role
    archive_role = mb / "archive" / args.role
    if not role_root.is_dir():
        print(f"missing role root: {role_root}", file=sys.stderr)
        return 1

    sources = collect_sources(role_root, args.epic)
    if not sources:
        print(f"nothing to archive for epic={args.epic} role={args.role}", file=sys.stderr)
        return 1

    print(f"==> archive epic={args.epic} role={args.role} items={len(sources)} dry_run={args.dry_run}")
    for src, rel in sources:
        dst = archive_role / rel
        move_tree(src, dst, args.dry_run)

    # After move, rewrite external refs
    n = 0
    for path in iter_rewrite_targets(mb, args.role, archive_role):
        if rewrite_file(path, args.role, args.epic, args.dry_run):
            n += 1
    print(f"==> rewritten files: {n}")
    print("==> reflection/ not moved (by design)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
