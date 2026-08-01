#!/usr/bin/env python3
"""Loop drift doctor + halt metrics from trace.jsonl."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def _norm(p: str | None) -> str:
    return (p or "").replace("\\", "/").strip().strip("`")


def _plan_id_from_artifact(artifact: str) -> str | None:
    m = re.search(r"/implement-([^/]+)/", artifact)
    if m:
        return m.group(1)
    m = re.search(r"/qa/([^/]+)/", artifact)
    if m:
        return m.group(1)
    return None


def foreign_result_errors(
    cwd: str | Path,
    *,
    role: str | None,
    plan_id: str | None,
    track: str = "epic",
) -> list[str]:
    """Fail-fast: finalized result belongs to another role/plan."""
    from session_result import load_result

    data = load_result(cwd, track=track)
    if not data:
        return []
    status = str(data.get("status") or "")
    if data.get("draft") is True or status in {"pending", "STUB", ""}:
        return []
    if status == "pending":
        return []
    errors: list[str] = []
    r_role = str(data.get("role") or "").upper()
    if role and r_role and r_role != str(role).upper():
        errors.append(f"result.role={r_role} expected={role}")
    art = _norm(str(data.get("artifact") or ""))
    if plan_id and art:
        art_plan = _plan_id_from_artifact(art)
        if art_plan and art_plan != plan_id:
            errors.append(
                f"result.artifact plan_id={art_plan} expected={plan_id} ({art})"
            )
        elif "/implement/" in art or "/qa/" in art:
            if f"implement-{plan_id}" not in art and f"/qa/{plan_id}/" not in art:
                # only flag when path looks epic-scoped but plan token missing
                if re.search(r"/implement-[^/]+/", art) or re.search(
                    r"/qa/[^/]+/", art
                ):
                    errors.append(
                        f"result.artifact foreign to plan_id={plan_id}: {art}"
                    )
    return errors


def reset_epic_result_stub(
    cwd: str | Path,
    *,
    role: str | None,
    mode: str | None = None,
    step_id: str | None = None,
    artifact: str | None = None,
) -> dict[str, Any]:
    """Clear any stale result.yaml and write a fresh stub for this epic."""
    from session_result import clear_result, load_result, write_stub_result

    cleared = clear_result(cwd, track="epic")
    path = write_stub_result(
        cwd,
        track="epic",
        role=role,
        mode=mode,
        step_id=step_id,
        artifact=artifact,
    )
    return {
        "cleared": cleared,
        "stub": str(path),
        "result": load_result(cwd, track="epic"),
    }


def halt_stats(cwd: str | Path, *, track: str = "epic", limit: int = 20) -> dict[str, Any]:
    """Aggregate halt / repair reasons from `.claude/runtime/{track}/trace.jsonl`."""
    path = Path(cwd) / ".claude" / "runtime" / track / "trace.jsonl"
    if not path.is_file():
        return {
            "ok": True,
            "track": track,
            "path": str(path),
            "total_lines": 0,
            "halt_total": 0,
            "top_halt_reasons": [],
            "top_kinds": [],
            "repair_total": 0,
        }
    kinds: Counter[str] = Counter()
    halt_reasons: Counter[str] = Counter()
    repair_reasons: Counter[str] = Counter()
    total = 0
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            kind = str(row.get("kind") or row.get("event") or "unknown")
            kinds[kind] += 1
            if kind == "halt":
                reason = str(row.get("reason") or row.get("halt_reason") or "?")
                halt_reasons[reason[:160]] += 1
            if kind == "repair":
                reason = str(row.get("reason") or "?")
                repair_reasons[reason[:160]] += 1
    return {
        "ok": True,
        "track": track,
        "path": str(path),
        "total_lines": total,
        "halt_total": sum(halt_reasons.values()),
        "top_halt_reasons": halt_reasons.most_common(limit),
        "repair_total": sum(repair_reasons.values()),
        "top_repair_reasons": repair_reasons.most_common(limit),
        "top_kinds": kinds.most_common(limit),
    }


def doctor(cwd: str | Path) -> dict[str, Any]:
    """Diff handoff × loop-state × decompose pending × result (+ halt stats)."""
    import epic_lib as el
    import loop_engine as le
    from session_result import load_result, validate_result

    cwd = Path(cwd)
    issues: list[dict[str, Any]] = []
    text = el.read_active_context(cwd)
    handoff = el.extract_handoff_block(text)
    load_now = el.extract_load_now(text)
    handoff_next = el.parse_next_command(handoff)
    handoff_mode = el.command_mode(handoff_next) if handoff_next else None

    ls = le.load_loop_state(cwd)
    ledger_cmd = le.command_from_state(ls)
    ledger_next = dict(ls.get("next") or {})
    epic = dict(ls.get("epic") or {})
    decompose = epic.get("decompose") or (el.load_epic_state(cwd).get("decompose"))
    pending_index = el.decompose_pending_left(cwd, decompose) if decompose else None
    pending_ledger = epic.get("pending")
    remaining = list(epic.get("remaining") or [])
    step = dict(ls.get("step") or {})

    if handoff_next and ledger_cmd and handoff_next != ledger_cmd:
        issues.append(
            {
                "kind": "handoff_vs_ledger",
                "severity": "warn",
                "handoff_next": handoff_next,
                "ledger_command": ledger_cmd,
                "note": "при конфликте побеждает loop-state (ledger)",
            }
        )

    if pending_index is not None and pending_ledger is not None:
        if int(pending_index) != int(pending_ledger):
            issues.append(
                {
                    "kind": "pending_drift",
                    "severity": "error",
                    "index_pending": pending_index,
                    "ledger_pending": pending_ledger,
                }
            )

    if remaining and step.get("id"):
        head = remaining[0].get("id") if isinstance(remaining[0], dict) else None
        if head and step.get("id") != head:
            issues.append(
                {
                    "kind": "step_vs_remaining_head",
                    "severity": "warn",
                    "step_id": step.get("id"),
                    "remaining_head": head,
                }
            )

    result = load_result(cwd, track="epic")
    result_errs = validate_result(result) if result else ["missing"]
    role = ls.get("role") or el.load_epic_state(cwd).get("role_prefix")
    plan_id = None
    if decompose:
        plan_id = el.epic_id_from_decompose_path(str(decompose))
    foreign = foreign_result_errors(cwd, role=role, plan_id=plan_id, track="epic")
    for msg in foreign:
        issues.append({"kind": "foreign_result", "severity": "error", "detail": msg})
    if result_errs and result and not result.get("draft"):
        issues.append(
            {
                "kind": "result_validate",
                "severity": "error",
                "errors": result_errs,
            }
        )

    shape = el.validate_active_context_shape(text) if text.strip() else ["empty"]
    for msg in shape:
        issues.append({"kind": "activeContext_shape", "severity": "error", "detail": msg})

    stats = halt_stats(cwd, track="epic")
    ok = not any(i.get("severity") == "error" for i in issues)
    return {
        "ok": ok,
        "issues": issues,
        "handoff": {
            "next": handoff_next,
            "mode": handoff_mode,
            "load_now": load_now[:5],
        },
        "ledger": {
            "command": ledger_cmd,
            "role": ls.get("role"),
            "mode": ls.get("mode"),
            "status": ls.get("status"),
            "step": step,
            "next": ledger_next,
            "pending": pending_ledger,
            "remaining_head": (remaining[0] if remaining else None),
            "decompose": decompose,
            "plan_id": plan_id,
        },
        "index": {"pending": pending_index},
        "result": {
            "data": result,
            "validate": result_errs,
            "foreign": foreign,
        },
        "halt_stats": stats,
    }
