#!/usr/bin/env python3
"""One-shot: migrate INTEG decompose/implement eNN *.md → *.yaml (v1-portal+)."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / ".claude" / "hooks") not in sys.path:
    sys.path.insert(0, str(ROOT / ".claude" / "hooks"))

from integ_yaml import CheckpointProgress, CheckpointSpec, compute_resume_from, seed_implement_checkpoints


def _bullets(block: str) -> list[str]:
    out: list[str] = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("- "):
            out.append(line[2:].strip())
        elif line.startswith("* "):
            out.append(line[2:].strip())
    return out


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


def _parse_grep_table(block: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in block.splitlines():
        if not line.strip().startswith("|"):
            continue
        if re.search(r"(?i)\|\s*back\s*\|", line):
            continue
        if re.match(r"^\|\s*[-:]+\s*\|", line):
            continue
        parts = [p.strip().strip("`") for p in line.strip().strip("|").split("|")]
        if len(parts) >= 2:
            rows.append({"back": parts[0], "front": parts[1]})
    return rows


def _parse_api_table(block: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in block.splitlines():
        if not line.strip().startswith("|"):
            continue
        if re.search(r"(?i)status\s*\|\s*detail", line):
            continue
        if re.match(r"^\|\s*[-:]+\s*\|", line):
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) >= 2:
            rows.append({"status": parts[0], "detail": parts[1]})
    return rows


def _parse_ui(block: str) -> dict[str, Any]:
    ui: dict[str, Any] = {}
    for line in _bullets(block):
        if "**route:**" in line.lower():
            ui["route"] = line.split(":", 1)[1].strip().strip("`")
        elif "**component(s):**" in line.lower():
            ui["components"] = line.split(":", 1)[1].strip()
        elif "**user sees:**" in line.lower():
            ui["user_sees"] = line.split(":", 1)[1].strip()
    if not ui and block.strip():
        ui["raw"] = block.strip()
    return ui


def _parse_contract(block: str) -> dict[str, Any]:
    contract: dict[str, Any] = {}
    for item in _bullets(block):
        low = item.lower()
        if "**method/path:**" in low:
            contract["method_path"] = item.split(":", 1)[-1].strip()
        elif "**query keys:**" in low:
            contract["query_keys"] = item.split(":", 1)[-1].strip()
        elif "**response shape:**" in low:
            contract["response_shape"] = item.split(":", 1)[-1].strip()
        elif "**front client:**" in low:
            contract["front_client"] = item.split(":", 1)[-1].strip()
        elif "**response header:**" in low:
            contract["response_header"] = item.split(":", 1)[-1].strip()
    if not contract and block.strip():
        contract["notes"] = block.strip()
    return contract


def _checklist_items(block: str) -> list[str]:
    items: list[str] = []
    for line in block.splitlines():
        line = line.strip()
        m = re.match(r"^- \[[ xX]\]\s*(.+)$", line)
        if m:
            items.append(m.group(1).strip())
    return items or _bullets(block)


def migrate_decompose(md_path: Path) -> dict[str, Any]:
    text = md_path.read_text(encoding="utf-8")
    title_m = re.match(r"(?im)^#\s+e(\d{2}):\s*(.+)$", text)
    step_id = f"e{title_m.group(1)}" if title_m else md_path.stem[:3]
    title = title_m.group(2).strip() if title_m else md_path.stem

    cp_block = _section(text, "Checkpoint")
    cp_lines = _bullets(cp_block)
    checkpoints = [
        {"id": f"cp{i + 1}", "criterion": ln.strip()}
        for i, ln in enumerate(cp_lines)
        if ln.strip() and not ln.strip().startswith("|")
    ]
    if not checkpoints:
        checkpoints = [{"id": "cp1", "criterion": "wire + verify per decompose §Verify"}]

    tdd_block = _section(text, "TDD")
    tdd = [ln for ln in tdd_block.splitlines() if re.match(r"^\d+\.", ln.strip())]

    data_block = _section(text, "§Data need")
    data_need = _bullets(data_block) or (data_block.strip() or None)

    return {
        "schema": "integ-decompose/v1",
        "step_id": step_id,
        "plan_id": _meta(text, "Plan ID") or "unknown",
        "title": title,
        "element_id": _meta(text, "Element ID") or step_id,
        "next_phase": _meta(text, "Next Phase") or "INTEG IMPLEMENT",
        "ui": _parse_ui(_section(text, "§UI")),
        "data_need": data_need if isinstance(data_need, list) and len(data_need) == 1 else data_need,
        "api_today": _parse_api_table(_section(text, "§API today")),
        "contract": _parse_contract(
            _section(text, "§Contract (lean — без кода)") or _section(text, "§Contract")
        ),
        "db": (_section(text, "§DB").strip() or None),
        "back": _checklist_items(_section(text, "§BACK")),
        "front": _checklist_items(_section(text, "§FRONT")),
        "grep_control": _parse_grep_table(_section(text, "§0.11")),
        "verify": _bullets(_section(text, "§Verify")),
        "tdd": tdd,
        "checkpoints": checkpoints,
    }


def migrate_implement(md_path: Path, decompose_data: dict[str, Any] | None) -> dict[str, Any]:
    text = md_path.read_text(encoding="utf-8")
    step_id = md_path.stem[:3] if md_path.stem.startswith("e") else md_path.stem
    title_m = re.match(r"(?im)^#\s+(.+)$", text)
    title = title_m.group(1).strip() if title_m else md_path.stem

    status_raw = _meta(text, "Статус") or "in_progress"
    status = "completed" if "completed" in status_raw.lower() else "in_progress"

    gaps_block = _section(text, "Gaps").strip()
    if gaps_block.lower() in {"нет", "none", "no"}:
        gaps: dict[str, Any] | str = {"status": "none"}
    else:
        gaps = {"status": "open", "notes": gaps_block}

    grep_block = _section(text, "Grep Control") or _section(text, "Grep Control (§0.11)")
    grep_rows = _parse_grep_table(grep_block)

    dec_specs = (
        [CheckpointSpec.model_validate(c) for c in decompose_data.get("checkpoints", [])]
        if decompose_data
        else []
    )
    if dec_specs:
        from integ_yaml import IntegDecomposeDoc

        dec = IntegDecomposeDoc.model_validate(decompose_data)
        seeded = seed_implement_checkpoints(dec, None)
        if status == "completed":
            for cp in seeded:
                cp.status = "done"
                cp.done_at = _meta(text, "Дата") or "2026-08-01"
        checkpoints = [cp.model_dump() for cp in seeded]
    else:
        checkpoints = [
            {
                "id": "cp1",
                "criterion": "wire + verify",
                "status": "done" if status == "completed" else "pending",
            }
        ]

    resume = compute_resume_from([CheckpointProgress.model_validate(c) for c in checkpoints])

    element_ref = _meta(text, "Element Ref") or ""
    if ".md" in element_ref:
        element_ref = re.sub(r"e(\d{2})-([^.]+)\.md", r"e\1-\2.yaml", element_ref)

    epic_id = decompose_data.get("plan_id") if decompose_data else "v1-portal"
    implement_index = f"memory-bank/integration/implement/implement-{epic_id}/index.md"

    return {
        "schema": "epic-implement/v1",
        "step_id": step_id,
        "plan_id": _meta(text, "Plan ID") or epic_id,
        "title": title,
        "status": status,
        "element_ref": element_ref
        or f"memory-bank/integration/plan/decompose-{epic_id}/{md_path.stem}.yaml",
        "implement_index": implement_index,
        "date": _meta(text, "Дата") or "2026-08-01",
        "skills_used": _bullets(_section(text, "Skills Used")),
        "discovery": _bullets(_section(text, "Discovery (фаза A)")),
        "gaps": gaps,
        "done": _bullets(_section(text, "Сделано")),
        "files": _bullets(_section(text, "Файлы")),
        "tests": _bullets(_section(text, "Тесты")),
        "integration_check": _bullets(_section(text, "Integration check")),
        "grep_control": grep_rows,
        "verification_results": _bullets(_section(text, "Verification Results")),
        "checkpoints": checkpoints,
        "resume_from": resume,
    }


def dump_yaml(data: dict[str, Any], path: Path) -> None:
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def migrate_tree(decompose_dir: Path, implement_dir: Path | None) -> int:
    count = 0
    dec_cache: dict[str, dict[str, Any]] = {}
    for md in sorted(decompose_dir.glob("e*.md")):
        data = migrate_decompose(md)
        out = md.with_suffix(".yaml")
        dump_yaml(data, out)
        dec_cache[md.stem] = data
        md.unlink()
        count += 1
        print(f"decompose → {out.relative_to(ROOT)}")

    if implement_dir and implement_dir.is_dir():
        for md in sorted(implement_dir.glob("e*.md")):
            dec = dec_cache.get(md.stem)
            if not dec:
                dec_path = decompose_dir / f"{md.stem}.yaml"
                if dec_path.is_file():
                    dec = yaml.safe_load(dec_path.read_text(encoding="utf-8"))
            data = migrate_implement(md, dec)
            out = md.with_suffix(".yaml")
            dump_yaml(data, out)
            md.unlink()
            count += 1
            print(f"implement → {out.relative_to(ROOT)}")
    return count


def patch_index_links(index_path: Path) -> None:
    if not index_path.is_file():
        return
    text = index_path.read_text(encoding="utf-8")
    text = re.sub(r"(e\d{2}-[a-z0-9-]+)\.md", r"\1.yaml", text)
    text = text.replace("eNN-*.yaml", "eNN-*.yaml")
    text = text.replace("integration-step.md", "integration-step.yaml")
    index_path.write_text(text, encoding="utf-8")
    print(f"index patched: {index_path}")


def main() -> int:
    dec = ROOT / "memory-bank/integration/plan/decompose-v1-portal"
    impl = ROOT / "memory-bank/integration/implement/implement-v1-portal"
    n = migrate_tree(dec, impl)
    patch_index_links(dec / "index.md")
    patch_index_links(impl / "index.md")
    print(f"migrated {n} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
