#!/usr/bin/env python3
"""Migrate epic shards *.md → *.yaml (BACK/FRONT sNN + INTEG eNN)."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))

from epic_yaml import (  # noqa: E402
    SCHEMA_EPIC_DECOMPOSE,
    SCHEMA_EPIC_IMPLEMENT,
    CheckpointProgress,
    compute_resume_from,
)
from migrate_integ_to_yaml import (  # noqa: E402
    migrate_decompose as migrate_integ_decompose,
    migrate_implement as migrate_integ_implement,
    patch_index_links,
)


def _section(text: str, name: str) -> str:
    pat = rf"(?ims)^##\s+{re.escape(name)}\s*$"
    m = re.search(pat, text)
    if not m:
        return ""
    rest = text[m.end() :]
    nxt = re.search(r"(?im)^##\s+", rest)
    return rest[: nxt.start()] if nxt else rest


def _meta(text: str, key: str) -> str | None:
    m = re.search(rf"(?im)^\*\*{re.escape(key)}:\*\*\s*(.+)$", text)
    return m.group(1).strip() if m else None


def _bullets(block: str) -> list[str]:
    out: list[str] = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("- "):
            out.append(line[2:].strip().strip("`"))
        elif line.startswith("* "):
            out.append(line[2:].strip())
    return out


def _checklist(block: str) -> list[str]:
    items: list[str] = []
    for line in block.splitlines():
        m = re.match(r"^- \[[ xX]\]\s*(.+)$", line.strip())
        if m:
            items.append(m.group(1).strip())
    return items or _bullets(block)


def _role_from_path(p: Path) -> str:
    parts = p.as_posix().split("/")
    if "integration" in parts:
        return "integ"
    if "front" in parts:
        return "front"
    return "back"


def migrate_role_decompose(md_path: Path) -> dict[str, Any]:
    text = md_path.read_text(encoding="utf-8")
    role = _role_from_path(md_path)
    title_m = re.match(r"(?im)^#\s+Шаг\s+(s\d{2}):\s*(.+)$", text)
    if not title_m:
        title_m = re.match(r"(?im)^#\s+(s\d{2}):\s*(.+)$", text)
    step_id = title_m.group(1).lower() if title_m else md_path.stem[:3]
    title = title_m.group(2).strip() if title_m else md_path.stem

    goal = _section(text, "Цель").strip() or title
    cp_criterion = goal.split("\n")[0][:200] if goal else "complete step AC"

    return {
        "schema": SCHEMA_EPIC_DECOMPOSE,
        "role": role,
        "step_id": step_id,
        "plan_id": _meta(text, "Plan ID") or "unknown",
        "title": title,
        "next_phase": _meta(text, "Next Phase") or f"{role.upper()} IMPLEMENT",
        "needs_creative": _meta(text, "needs_creative") or "no",
        "goal": goal,
        "context": {
            "consumes": _bullets(_section(text, "Контекст")),
            "files": _bullets(_section(text, "Файлы")),
        },
        "checkpoints": [{"id": "cp1", "criterion": cp_criterion}],
        "verify": _bullets(_section(text, "Verify")) or _bullets(_section(text, "TDD")),
        "tdd": [ln.strip() for ln in _section(text, "TDD").splitlines() if re.match(r"^\d+\.", ln.strip())],
    }


def migrate_role_implement(md_path: Path, decompose_data: dict[str, Any] | None) -> dict[str, Any]:
    text = md_path.read_text(encoding="utf-8")
    role = _role_from_path(md_path)
    step_id = md_path.stem[:3] if md_path.stem.startswith("s") else md_path.stem
    title_m = re.match(r"(?im)^#\s+(.+)$", text)
    title = title_m.group(1).strip() if title_m else md_path.stem

    status_raw = _meta(text, "Статус") or "in_progress"
    status = "completed" if "completed" in status_raw.lower() else "in_progress"

    task_m = re.match(r"(?i)T-(\d+)", title)
    task_id = f"T-{task_m.group(1)}" if task_m else None

    decompose_ref = _meta(text, "Decompose step") or ""
    m = re.search(r"\(([^)]+)\)", decompose_ref)
    dec_rel = m.group(1) if m else decompose_ref
    if dec_rel.endswith(".md"):
        dec_rel = dec_rel[:-3] + ".yaml"

    plan_id = _meta(text, "Plan ID") or "unknown"
    role_dir = "integration" if role == "integ" else role
    implement_index = f"memory-bank/{role_dir}/implement/implement-{plan_id}/index.md"

    if decompose_data and decompose_data.get("checkpoints"):
        checkpoints = []
        for spec in decompose_data["checkpoints"]:
            checkpoints.append(
                {
                    "id": spec["id"],
                    "criterion": spec.get("criterion", "step"),
                    "status": "done" if status == "completed" else "pending",
                    "done_at": "2026-08-01" if status == "completed" else None,
                    "notes": None,
                }
            )
    else:
        checkpoints = [
            {
                "id": "cp1",
                "criterion": "step AC complete",
                "status": "done" if status == "completed" else "pending",
                "done_at": "2026-08-01" if status == "completed" else None,
            }
        ]

    data: dict[str, Any] = {
        "schema": SCHEMA_EPIC_IMPLEMENT,
        "role": role,
        "step_id": step_id,
        "plan_id": plan_id,
        "title": title,
        "status": status,
        "decompose_ref": dec_rel or f"memory-bank/{role_dir}/plan/decompose-{plan_id}/{md_path.stem}.yaml",
        "implement_index": implement_index,
        "date": (_meta(text, "Дата") or "2026-08-01").strip(),
        "level": _meta(text, "Уровень"),
        "task_id": task_id,
        "done": _bullets(_section(text, "Сделано")),
        "files": _bullets(_section(text, "Файлы")),
        "tests": _bullets(_section(text, "Тесты")),
        "integration_check": _checklist(_section(text, "Integration check")),
        "checkpoints": checkpoints,
        "resume_from": compute_resume_from(
            [CheckpointProgress.model_validate(c) for c in checkpoints]
        ),
    }
    if task_id:
        data["task_id"] = task_id
    return data


def dump_yaml(data: dict[str, Any], out: Path) -> None:
    out.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def migrate_tree(base: Path) -> int:
    count = 0
    for md in sorted(base.rglob("*.md")):
        if md.name == "index.md":
            continue
        name = md.name.lower()
        if not (name.startswith("s") or name.startswith("e")):
            continue
        if name.startswith("e"):
            if "/plan/decompose-" in md.as_posix():
                data = migrate_integ_decompose(md)
            else:
                dec = md.with_name(md.name).parent.parent.parent / "plan" / md.parent.name.replace("implement-", "decompose-")
                dec_md = dec / md.name if (dec / md.name).is_file() else None
                dec_data = migrate_integ_decompose(dec_md) if dec_md else None
                data = migrate_integ_implement(md, dec_data)
            if data.get("schema") == "integ-decompose/v1":
                data["schema"] = SCHEMA_EPIC_DECOMPOSE
                data.setdefault("role", "integ")
            if data.get("schema") == "epic-implement/v1":
                data["schema"] = SCHEMA_EPIC_IMPLEMENT
                data.setdefault("role", "integ")
                if data.get("element_ref") and not data.get("decompose_ref"):
                    data["decompose_ref"] = data["element_ref"]
        else:
            if "/plan/decompose-" in md.as_posix():
                data = migrate_role_decompose(md)
            else:
                parts = md.parts
                dec_dir = None
                for i, p in enumerate(parts):
                    if p.startswith("decompose-"):
                        dec_dir = Path(*parts[: i + 1])
                        break
                dec_md = (dec_dir / md.name) if dec_dir and (dec_dir / md.name).is_file() else None
                dec_data = migrate_role_decompose(dec_md) if dec_md else None
                data = migrate_role_implement(md, dec_data)
        out = md.with_suffix(".yaml")
        dump_yaml(data, out)
        md.unlink()
        count += 1
        print(f"→ {out.relative_to(ROOT)}")
    return count


def main() -> int:
    roots = [
        ROOT / "memory-bank/back/plan",
        ROOT / "memory-bank/back/implement",
        ROOT / "memory-bank/front/plan",
        ROOT / "memory-bank/front/implement",
        ROOT / "memory-bank/integration/plan",
        ROOT / "memory-bank/integration/implement",
    ]
    total = 0
    for r in roots:
        if r.is_dir():
            total += migrate_tree(r)
    for idx in ROOT.glob("memory-bank/**/decompose-*/index.md"):
        patch_index_links(idx)
    for idx in ROOT.glob("memory-bank/**/implement-*/index.md"):
        patch_index_links(idx)
    print(f"migrated {total} shard files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
