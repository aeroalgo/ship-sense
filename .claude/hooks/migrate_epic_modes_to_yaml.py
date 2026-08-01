#!/usr/bin/env python3
"""Migrate epic QA + REFACTOR implement shards *.md → *.yaml."""
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

from epic_shard_extra import SCHEMA_EPIC_QA, SCHEMA_EPIC_REFACTOR  # noqa: E402
from epic_yaml import compute_resume_from, CheckpointProgress  # noqa: E402


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


def _meta_line(text: str, key: str) -> str | None:
    m = re.search(rf"(?im)^-\s+\*\*{re.escape(key)}:\*\*\s*(.+)$", text)
    return m.group(1).strip() if m else None


def _bullets(block: str) -> list[str]:
    out: list[str] = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("- "):
            out.append(line[2:].strip().strip("`"))
    return out


def _checklist(block: str) -> list[str]:
    items: list[str] = []
    for line in block.splitlines():
        m = re.match(r"^- \[[ xX]\]\s*(.+)$", line.strip())
        if m:
            items.append(m.group(1).strip())
    return items or _bullets(block)


def _table_rows(block: str, min_cols: int = 2) -> list[dict[str, str]]:
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    if len(lines) < 2:
        return []
    header = [c.strip().lower() for c in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for ln in lines[2:]:
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) < min_cols:
            continue
        row = {header[i]: cells[i] for i in range(min(len(header), len(cells)))}
        rows.append(row)
    return rows


def _role_from_path(p: Path) -> str:
    parts = p.as_posix().split("/")
    if "integration" in parts:
        return "integ"
    if "front" in parts:
        return "front"
    return "back"


def migrate_qa(md_path: Path) -> dict[str, Any]:
    text = md_path.read_text(encoding="utf-8")
    role = _role_from_path(md_path)
    title_m = re.match(r"(?im)^#\s+(.+?)\s+REVIEW\s*$", text)
    title = title_m.group(1).strip() if title_m else md_path.stem

    task_m = re.match(r"(?i)T-(\d+)", title)
    task_id = f"T-{task_m.group(1)}" if task_m else None

    verdict = (_meta(text, "Verdict") or "pass").strip().lower()
    if verdict not in {"pass", "fail", "blocked"}:
        verdict = "pass"

    scope = _bullets(_section(text, "Scope"))
    checks = _checklist(_section(text, "Checks"))
    blockers = _bullets(_section(text, "Blockers"))
    limitations = _bullets(_section(text, "Ограничения QA"))

    issues: list[dict[str, str]] = []
    for row in _table_rows(_section(text, "Issues")):
        if row.get("id", "—") in {"—", "-", ""}:
            continue
        issues.append(
            {
                "id": row.get("id", ""),
                "sev": row.get("sev", ""),
                "file": row.get("file", ""),
                "msg": row.get("msg", ""),
            }
        )

    fix_plan: list[dict[str, str]] = []
    fp_block = _section(text, "Fix plan")
    if not fp_block.strip():
        fp_block = _section(text, "Fix plan (обязательно при verdict")
    for row in _table_rows(fp_block, min_cols=3):
        issue = row.get("issue") or row.get("#", "")
        if not issue or issue in {"—", "-"}:
            continue
        fix_plan.append(
            {
                "issue": issue,
                "command": row.get("command", ""),
                "subject": row.get("subject", ""),
                "scope": row.get("scope / files") or row.get("scope", ""),
                "verify": row.get("verify", ""),
            }
        )

    suite: list[str] = []
    for chk in checks:
        if ".venv/bin/pytest" in chk or "vitest" in chk or "playwright" in chk:
            suite.append(chk)

    epic_id = None
    plan_id = None
    for item in scope:
        em = re.search(r"epic:\s*`?([a-z0-9-]+)`?", item, re.I)
        if em:
            epic_id = em.group(1)
            plan_id = epic_id
        pm = re.search(r"plan_id:\s*`?([a-z0-9-]+)`?", item, re.I)
        if pm:
            plan_id = pm.group(1)
    if not plan_id:
        plan_id = md_path.parent.name

    data: dict[str, Any] = {
        "schema": SCHEMA_EPIC_QA,
        "role": role,
        "date": (_meta(text, "Дата") or "2026-08-01").strip(),
        "reviewer": (_meta(text, "Reviewer") or f"{role.upper()} QA").strip(),
        "verdict": verdict,
        "scope": scope or [f"epic: {plan_id}"],
        "checks": checks or ["migrated from md — review checks"],
        "issues": issues,
        "blockers": blockers,
        "fix_plan": fix_plan,
        "limitations": limitations,
        "suite": suite,
        "plan_id": plan_id,
        "epic_id": epic_id or plan_id,
    }
    if task_id:
        data["task_id"] = task_id
    return data


def migrate_refactor_implement(md_path: Path) -> dict[str, Any]:
    text = md_path.read_text(encoding="utf-8")
    role = _role_from_path(md_path)
    step_id = md_path.stem[:3].lower()
    title_m = re.match(r"(?im)^#\s+(.+)$", text)
    title = title_m.group(1).strip() if title_m else md_path.stem

    epic = _meta_line(text, "Epic") or _meta(text, "Epic") or "unknown"
    epic = epic.strip("`")

    status_raw = _meta(text, "Статус") or "in_progress"
    status = "completed" if "completed" in status_raw.lower() else "in_progress"

    behavior = _meta(text, "Behavior freeze") or _meta_line(text, "Behavior freeze") or ""
    if not behavior:
        bf_block = re.search(r"(?im)behavior freeze:\*\*\s*(.+)$", text)
        if bf_block:
            behavior = bf_block.group(1).strip()

    files_block = _section(text, "Реализация / Файлы") or _section(text, "Файлы")
    tests_block = _section(text, "Верификация / Тесты") or _section(text, "Тесты")
    file_items = _bullets(files_block)
    test_items = _bullets(tests_block)

    checkpoints = [
        {
            "id": "cp1",
            "criterion": "refactor AC + behavior freeze",
            "status": "done" if status == "completed" else "pending",
            "done_at": "2026-08-01" if status == "completed" else None,
        }
    ]

    role_dir = "integration" if role == "integ" else role
    dec_rel = (
        f"memory-bank/{role_dir}/refactor/plan/decompose-{epic}/{md_path.stem}.yaml"
    )

    return {
        "schema": SCHEMA_EPIC_REFACTOR,
        "role": role,
        "step_id": step_id,
        "plan_id": epic,
        "title": title,
        "status": status,
        "date": (_meta_line(text, "Дата") or _meta(text, "Дата") or "2026-08-01").strip(),
        "behavior_freeze": behavior or "preserve external behavior",
        "decompose_ref": dec_rel,
        "done": file_items[:10] or ["refactor step complete"],
        "files": file_items or ["migrated — review paths"],
        "tests": test_items or ["migrated — review tests"],
        "checkpoints": checkpoints,
        "resume_from": compute_resume_from(
            [CheckpointProgress.model_validate(c) for c in checkpoints]
        ),
    }


def dump_yaml(data: dict[str, Any], out: Path) -> None:
    out.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def migrate_qa_tree(base: Path) -> int:
    count = 0
    for md in sorted(base.rglob("qa-*.md")):
        if "/qa/" not in md.as_posix():
            continue
        data = migrate_qa(md)
        out = md.with_suffix(".yaml")
        dump_yaml(data, out)
        md.unlink()
        count += 1
        print(f"→ {out.relative_to(ROOT)}")
    return count


def migrate_refactor_tree(base: Path) -> int:
    count = 0
    for md in sorted(base.rglob("r*.md")):
        if "/refactor/implement/" not in md.as_posix():
            continue
        if not re.match(r"(?i)^r\d{2}-", md.name):
            continue
        data = migrate_refactor_implement(md)
        out = md.with_suffix(".yaml")
        dump_yaml(data, out)
        md.unlink()
        count += 1
        print(f"→ {out.relative_to(ROOT)}")
    return count


def main() -> int:
    total = 0
    mb = ROOT / "memory-bank"
    total += migrate_qa_tree(mb)
    total += migrate_refactor_tree(mb)
    print(f"migrated {total} qa/refactor shard files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
