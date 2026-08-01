#!/usr/bin/env python3
"""Program loop — cross-role journey FSM above epic-loop.

Epic-loop = one role × one decompose.
Program-loop = BACK/FRONT/INTEG fanout (GAP queue) + resume.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import epic_lib as el

PROGRAM_DIRNAME = "program"
STATE_NAME = "state.json"
NEXT_PROMPT_NAME = "next-prompt.txt"
QUEUE_NAME = "queue.json"

PHASES = (
    "INTEG_PLAN",
    "INTEG_DECOMPOSE",
    "INTEG_STEPS",
    "GAP_OPEN",
    "GAP_FANOUT",
    "GAP_JOIN",
    "GAP_CLOSE",
    "INTEG_RESUME",
    "INTEG_QA",
    "INTEG_REFLECT",
    "COMPLETE",
    "HALT",
)

# G-FB* = front needs back → BACK work first
# G-BF* = back needs front → FRONT work after BACK
GAP_ID_RE = re.compile(r"\b(G-(?:BF|FB)\d+)\b", re.I)
PLAN_LINK_RE = re.compile(
    r"\[([^\]]*(?:plan-(?:BACK|FRONT)-GAP-[^\]]*)?)\]\(([^)]+)\)",
    re.I,
)
STATUS_RE = re.compile(r"\b(open|pending|done|closed|blocked|active)\b", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def program_dir(cwd: str | Path) -> Path:
    d = Path(cwd) / ".claude" / "runtime" / PROGRAM_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def state_path(cwd: str | Path) -> Path:
    return program_dir(cwd) / STATE_NAME


def next_prompt_path(cwd: str | Path) -> Path:
    return program_dir(cwd) / NEXT_PROMPT_NAME


def queue_path(cwd: str | Path) -> Path:
    return program_dir(cwd) / QUEUE_NAME


def default_state() -> dict[str, Any]:
    return {
        "active": False,
        "status": "idle",
        "phase": None,
        "program_id": None,
        "integ_decompose": None,
        "integ_plan": None,
        "gap_path": None,
        "resume": None,
        "queue": [],
        "current_action": None,
        "started_at": None,
        "updated_at": None,
        "iteration": 0,
        "max_iterations": 80,
        "halt_reason": None,
        "last_fingerprint": None,
        "model": None,
        "history": [],
    }


def load_program_state(cwd: str | Path) -> dict[str, Any]:
    p = state_path(cwd)
    st = default_state()
    if not p.is_file():
        return st
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        for k, v in st.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return st


def save_program_state(cwd: str | Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    state_path(cwd).write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    queue_path(cwd).write_text(
        json.dumps(state.get("queue") or [], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _sync_program_to_loop(cwd, state)


def _sync_program_to_loop(cwd: str | Path, st: dict[str, Any]) -> None:
    try:
        import loop_engine as le
    except Exception:
        return
    try:
        text = el.read_active_context(cwd)
        handoff = el.extract_handoff_block(text)
        load = el.extract_load_now(text)
        ls = le.sync_from_handoff(
            cwd,
            handoff,
            load_now=load,
            decompose=st.get("integ_decompose"),
            pending=el.decompose_pending_left(cwd, st.get("integ_decompose")),
            model=st.get("model"),
            journey_id=st.get("program_id"),
            save=False,
        )
        journey = dict(ls.get("journey") or {})
        if st.get("phase"):
            journey["phase"] = str(st["phase"]).upper()
        journey["id"] = st.get("program_id")
        ls["journey"] = journey
        ls["queue"] = list(st.get("queue") or [])
        if st.get("gap_path"):
            resume = dict(ls.get("resume") or {})
            resume["gap"] = st["gap_path"]
            ls["resume"] = resume
        if st.get("resume"):
            resume = dict(ls.get("resume") or {})
            resume.update({k: v for k, v in st["resume"].items() if v})
            ls["resume"] = resume
        ls["active"] = bool(st.get("active"))
        ls["status"] = st.get("status") or ls.get("status")
        le.save_loop_state(cwd, ls)
    except Exception:
        return


def _norm_mb_path(raw: str, *, hint: str | None = None) -> str:
    p = raw.strip().strip("`").rstrip("/")
    if p.startswith("../"):
        p = _collapse_rel(p, base="memory-bank/integration/gap")
    if p.startswith("memory-bank/"):
        return p
    if p.startswith("back/") or p.startswith("front/") or p.startswith("integration/"):
        return f"memory-bank/{p}"
    if "plan-BACK-GAP" in p or "/back/plan/" in p:
        return f"memory-bank/back/plan/{Path(p).name}"
    if "plan-FRONT-GAP" in p or "/front/plan/" in p:
        return f"memory-bank/front/plan/{Path(p).name}"
    if hint:
        return hint
    return p


def _collapse_rel(rel: str, *, base: str) -> str:
    cur = Path(base)
    for part in Path(rel).parts:
        if part == "..":
            cur = cur.parent
        elif part == ".":
            continue
        else:
            cur = cur / part
    return str(cur.as_posix())


def role_for_gap_id(gap_id: str) -> str:
    gid = gap_id.upper()
    if gid.startswith("G-FB"):
        return "BACK"
    if gid.startswith("G-BF"):
        return "FRONT"
    return "INTEG"


def parse_gap_queue(gap_text: str) -> list[dict[str, Any]]:
    """Build work queue from gap markdown (G-BF* / G-FB* tables + plan links)."""
    items: dict[str, dict[str, Any]] = {}
    last_id: str | None = None

    def ensure(gid: str) -> dict[str, Any]:
        return items.setdefault(
            gid,
            {
                "id": gid,
                "role": role_for_gap_id(gid),
                "status": "pending",
                "needs": ["PLAN", "DECOMPOSE", "EPIC"],
                "plan": None,
                "decompose": None,
                "after": [],
            },
        )

    def apply_links(item: dict[str, Any], line: str) -> None:
        for _label, href in PLAN_LINK_RE.findall(line):
            href_l = href.lower()
            if "plan-back-gap" in href_l or "/back/plan/" in href_l:
                item["plan"] = _norm_mb_path(href)
            elif "plan-front-gap" in href_l or "/front/plan/" in href_l:
                item["plan"] = _norm_mb_path(href)
            elif "decompose-" in href_l:
                item["decompose"] = _norm_mb_path(href)

    for line in gap_text.splitlines():
        ids = GAP_ID_RE.findall(line)
        if ids:
            for raw_id in ids:
                gid = raw_id.upper()
                last_id = gid
                item = ensure(gid)
                apply_links(item, line)
                st = STATUS_RE.findall(line)
                if st:
                    last = st[-1].lower()
                    if last in {"done", "closed"}:
                        item["status"] = "done"
                    elif last == "blocked":
                        item["status"] = "blocked"
                    elif last in {"open", "pending", "active"} and item["status"] == "pending":
                        item["status"] = "pending"
            continue

        # plan/decompose links on following lines belong to last gap id
        if last_id and ("plan-" in line.lower() or "decompose-" in line.lower() or "](" in line):
            apply_links(ensure(last_id), line)

    # BACK (G-FB) before FRONT (G-BF); FRONT waits on all BACK items
    ordered = sorted(
        items.values(),
        key=lambda it: (0 if it["role"] == "BACK" else 1 if it["role"] == "FRONT" else 2, it["id"]),
    )
    back_ids = [it["id"] for it in ordered if it["role"] == "BACK"]
    for it in ordered:
        if it["role"] == "FRONT" and back_ids:
            it["after"] = list(back_ids)
    return ordered


def load_gap_file(cwd: str | Path, gap_rel: str) -> str:
    p = Path(cwd) / gap_rel
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def extract_program_fields(handoff: str) -> dict[str, str | None]:
    def one(pat: str) -> str | None:
        m = re.search(pat, handoff)
        if not m:
            return None
        return m.group(1).strip().strip("`")

    return {
        "program": one(r"(?im)^\s*[-*]\s*\*\*Program:\*\*\s*(.+)$"),
        "resume": one(r"(?im)^\s*[-*]\s*\*\*Resume:\*\*\s*(.+)$"),
        "gap": one(r"(?im)^\s*[-*]\s*\*\*Gap:\*\*\s*(.+)$"),
        "queue_ref": one(r"(?im)^\s*[-*]\s*\*\*Queue:\*\*\s*(.+)$"),
    }


def parse_resume(raw: str | None) -> dict[str, str] | None:
    if not raw:
        return None
    # INTEG GAP CLOSE @path  OR  INTEG IMPLEMENT @e03
    m = re.search(
        rf"(?i)\b((?:BACK|FRONT|INTEG)\s+(?:{el._MODE_ALT}))\b(?:\s+@\s*(\S+))?",
        raw,
    )
    if not m:
        return None
    cmd = el._normalize_cmd(m.group(1))
    target = (m.group(2) or "").strip("`'\"")
    out: dict[str, str] = {"command": cmd}
    if target:
        if "implement/" in target or target.endswith(".md"):
            out["implement"] = _norm_mb_path(target)
        else:
            out["target"] = target
    return out


def deps_satisfied(item: dict[str, Any], queue: list[dict[str, Any]]) -> bool:
    by_id = {q["id"]: q for q in queue}
    for dep in item.get("after") or []:
        other = by_id.get(dep)
        if not other or other.get("status") != "done":
            return False
    return True


def next_queue_item(queue: list[dict[str, Any]]) -> dict[str, Any] | None:
    for it in queue:
        if it.get("status") in {"done", "blocked"}:
            continue
        if not deps_satisfied(it, queue):
            continue
        return it
    return None


def queue_all_done(queue: list[dict[str, Any]]) -> bool:
    if not queue:
        return True
    return all(it.get("status") == "done" for it in queue)


def arm_program(
    cwd: str | Path,
    *,
    program_id: str,
    phase: str = "INTEG_STEPS",
    integ_decompose: str | None = None,
    integ_plan: str | None = None,
    gap_path: str | None = None,
    resume: dict[str, str] | None = None,
    max_iterations: int = 80,
    model: str | None = None,
) -> dict[str, Any]:
    if phase not in PHASES:
        raise ValueError(f"unknown phase: {phase}")

    st = default_state()
    st["active"] = True
    st["status"] = "running"
    st["phase"] = phase
    st["program_id"] = program_id
    st["integ_decompose"] = (
        el.normalize_decompose_ref(cwd, integ_decompose) if integ_decompose else None
    )
    st["integ_plan"] = integ_plan
    st["gap_path"] = gap_path
    st["resume"] = resume
    st["started_at"] = utc_now()
    st["iteration"] = 0
    st["max_iterations"] = max_iterations
    st["last_fingerprint"] = el.fingerprint_context(el.read_active_context(cwd))
    if model:
        st["model"] = model.strip()

    if gap_path:
        text = load_gap_file(cwd, gap_path)
        st["queue"] = parse_gap_queue(text)
        if phase == "INTEG_STEPS":
            st["phase"] = "GAP_FANOUT"

    save_program_state(cwd, st)
    return st


def halt_program(cwd: str | Path, reason: str) -> dict[str, Any]:
    st = load_program_state(cwd)
    st["active"] = False
    st["status"] = "halted"
    st["phase"] = "HALT"
    st["halt_reason"] = reason
    save_program_state(cwd, st)
    return st


def complete_program(cwd: str | Path, reason: str = "journey complete") -> dict[str, Any]:
    st = load_program_state(cwd)
    st["active"] = False
    st["status"] = "complete"
    st["phase"] = "COMPLETE"
    st["halt_reason"] = reason
    st["current_action"] = None
    save_program_state(cwd, st)
    return st


def _action(
    *,
    kind: str,
    phase: str,
    role: str,
    command: str,
    decompose: str | None = None,
    artifact: str | None = None,
    gap_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "phase": phase,
        "role": role,
        "command": command,
        "decompose": decompose,
        "artifact": artifact,
        "gap_id": gap_id,
        "reason": reason,
    }


def _fanout_action(item: dict[str, Any], phase: str) -> dict[str, Any]:
    role = item["role"]
    status = item.get("status") or "pending"
    plan = item.get("plan")
    decompose = item.get("decompose")

    if status == "pending":
        return _action(
            kind="mode",
            phase=phase,
            role=role,
            command=f"{role} PLAN",
            artifact=plan,
            gap_id=item["id"],
            reason=f"queue {item['id']}: PLAN",
        )
    if status == "plan":
        return _action(
            kind="mode",
            phase=phase,
            role=role,
            command=f"{role} DECOMPOSE",
            artifact=plan,
            gap_id=item["id"],
            reason=f"queue {item['id']}: DECOMPOSE",
        )
    if status in {"decompose", "epic"}:
        dec = decompose
        if not dec and plan:
            # convention: plan-BACK-GAP-x → decompose-BACK-GAP-x
            name = Path(plan).stem.replace("plan-", "decompose-", 1)
            dec = str(Path(plan).parent / name)
        return _action(
            kind="epic",
            phase=phase,
            role=role,
            command=f"{role} IMPLEMENT",
            decompose=dec,
            gap_id=item["id"],
            reason=f"queue {item['id']}: EPIC",
        )
    return _action(
        kind="halt",
        phase="HALT",
        role=role,
        command="",
        gap_id=item["id"],
        reason=f"queue {item['id']}: unknown status {status}",
    )


def build_program_prompt(action: dict[str, Any], cwd: str | Path, st: dict[str, Any]) -> str:
    cmd = action["command"]
    role = action["role"]
    load_now: list[str] = []
    if action.get("artifact"):
        load_now.append(action["artifact"])
    if action.get("decompose"):
        load_now.append(action["decompose"])
    resume = st.get("resume") or {}
    if resume.get("implement"):
        load_now.append(resume["implement"])
    if st.get("gap_path"):
        load_now.append(st["gap_path"])

    # reuse epic prompt packing for IMPLEMENT/QA/…; for PLAN/DECOMPOSE/GAP add program header
    mode = el.command_mode(cmd) or ""
    if mode in {"IMPLEMENT", "REFACTOR", "QA", "BUGFIX", "CREATIVE", "REFLECT"}:
        base = el.build_prompt(cmd, cwd, load_now)
    else:
        lines = [
            cmd,
            "",
            "PROGRAM MODE (journey): ровно один atomic mode-шаг в этой сессии.",
            "После FINISH: Write весь activeContext (load_now → 1× ## Handoff → ≤1× ## done).",
            "Добавь поля если применимо:",
            f"- **Program:** {st.get('phase')}",
            f"- **Gap:** `{st.get('gap_path') or ''}`".rstrip(),
        ]
        if st.get("resume"):
            lines.append(f"- **Resume:** `{json.dumps(st['resume'], ensure_ascii=False)}`")
        if action.get("gap_id"):
            lines.append(f"- **Queue item:** {action['gap_id']} ({action.get('reason')})")
        lines.append("")
        lines.append("Старт:")
        lines.append("1. memory-bank/activeContext.md → load_now + §Handoff")
        for i, p in enumerate(load_now[:3], start=2):
            lines.append(f"{i}. `{p}`")
        if mode in {"GAP", "GAP CLOSE"}:
            lines.extend(
                [
                    "",
                    "## PROGRAM GAP contract",
                    "GAP: gap-*.md + plan-BACK-GAP / plan-FRONT-GAP + REWRITE §Gaps → link.",
                    "FINISH Handoff обязателен:",
                    "- **Следующий:** (см. ниже)",
                    "- **Program:** GAP_FANOUT",
                    "- **Gap:** `memory-bank/integration/gap/<epic_id>/gap-….md`",
                    "- **Resume:** `INTEG GAP CLOSE @<implement eNN>`",
                    "Следующий после GAP: первый queue item PLAN (program сам переключит роль).",
                    "FORBIDDEN: вручную стартовать BACK/FRONT epic в этой сессии.",
                ]
            )
        if mode == "PLAN":
            lines.extend(
                [
                    "",
                    f"## PROGRAM {role} PLAN (GAP close-out)",
                    f"Пиши plan в memory-bank/{role.lower()}/plan/ (plan-*-GAP-* если gap item).",
                    f"FINISH: `- **Следующий:** {role} DECOMPOSE` + **Program:** GAP_FANOUT.",
                ]
            )
        if mode == "DECOMPOSE":
            lines.extend(
                [
                    "",
                    f"## PROGRAM {role} DECOMPOSE",
                    "Один проход: index + все sNN/eNN. FINISH:",
                    f"`- **Следующий:** {role} IMPLEMENT` + **Program:** GAP_FANOUT.",
                    "Epic прогонит program-loop (не начинай s02 в этой сессии).",
                ]
            )
        base = "\n".join(lines)

    header = [
        "PROGRAM JOURNEY ACTIVE",
        f"phase={st.get('phase')} program_id={st.get('program_id')} action={action.get('kind')}",
        f"reason={action.get('reason') or ''}",
        "",
    ]
    return "\n".join(header) + base


def resolve_next(cwd: str | Path) -> dict[str, Any]:
    st = load_program_state(cwd)
    if not st.get("active") or st.get("status") != "running":
        return {
            "ok": False,
            "status": st.get("status") or "idle",
            "action": None,
            "prompt": None,
            "reason": st.get("halt_reason") or "program not running",
        }

    if int(st.get("iteration") or 0) >= int(st.get("max_iterations") or 80):
        halt_program(cwd, f"max_iterations={st.get('max_iterations')}")
        return {
            "ok": False,
            "status": "halted",
            "action": None,
            "prompt": None,
            "reason": "max_iterations reached",
        }

    phase = st.get("phase") or "INTEG_STEPS"
    text = el.read_active_context(cwd)
    handoff = el.extract_handoff_block(text)
    fields = extract_program_fields(handoff)
    next_cmd = el.parse_next_command(handoff)

    if el.HALT_RE.search(handoff):
        halt_program(cwd, "human gate in Handoff")
        return {
            "ok": False,
            "status": "halted",
            "action": None,
            "prompt": None,
            "reason": "human/grill-me gate",
        }

    # Sync gap path / resume from handoff
    if fields.get("gap"):
        gp = _norm_mb_path(fields["gap"] or "")
        if gp.endswith(".md"):
            st["gap_path"] = gp
    if fields.get("resume"):
        parsed = parse_resume(fields["resume"])
        if parsed:
            st["resume"] = parsed
    if fields.get("program"):
        prog = (fields["program"] or "").strip().upper().replace(" ", "_")
        if prog in PHASES:
            # trust explicit Program only when not mid-fanout item
            if phase in {"INTEG_STEPS", "GAP_OPEN", "INTEG_RESUME"} or prog == "GAP_FANOUT":
                if prog != phase and prog in {
                    "GAP_FANOUT",
                    "GAP_CLOSE",
                    "INTEG_RESUME",
                    "INTEG_QA",
                }:
                    phase = prog
                    st["phase"] = phase

    # If Handoff says INTEG GAP while in steps → open gap
    if next_cmd and el.command_mode(next_cmd) == "GAP" and phase in {
        "INTEG_STEPS",
        "INTEG_RESUME",
    }:
        phase = "GAP_OPEN"
        st["phase"] = phase

    if next_cmd and el.command_mode(next_cmd) == "GAP CLOSE" and phase in {
        "GAP_JOIN",
        "GAP_FANOUT",
        "GAP_OPEN",
    }:
        if queue_all_done(st.get("queue") or []):
            phase = "GAP_CLOSE"
            st["phase"] = phase

    action: dict[str, Any] | None = None

    if phase == "INTEG_PLAN":
        action = _action(
            kind="mode",
            phase=phase,
            role="INTEG",
            command="INTEG PLAN",
            artifact=st.get("integ_plan"),
            reason="journey: INTEG PLAN",
        )
    elif phase == "INTEG_DECOMPOSE":
        action = _action(
            kind="mode",
            phase=phase,
            role="INTEG",
            command="INTEG DECOMPOSE",
            artifact=st.get("integ_plan"),
            reason="journey: INTEG DECOMPOSE",
        )
    elif phase in {"INTEG_STEPS", "INTEG_RESUME"}:
        dec = st.get("integ_decompose")
        if not dec:
            halt_program(cwd, "integ_decompose missing")
            return {
                "ok": False,
                "status": "halted",
                "action": None,
                "prompt": None,
                "reason": "integ_decompose missing",
            }
        action = _action(
            kind="epic",
            phase=phase,
            role="INTEG",
            command="INTEG IMPLEMENT",
            decompose=dec,
            reason="journey: INTEG epic steps",
        )
    elif phase == "GAP_OPEN":
        action = _action(
            kind="mode",
            phase=phase,
            role="INTEG",
            command="INTEG GAP",
            artifact=(st.get("resume") or {}).get("implement"),
            reason="journey: open GAP + build queue",
        )
    elif phase == "GAP_FANOUT":
        if st.get("gap_path") and not (st.get("queue") or []):
            st["queue"] = parse_gap_queue(load_gap_file(cwd, st["gap_path"]))
        item = next_queue_item(st.get("queue") or [])
        if item is None:
            if queue_all_done(st.get("queue") or []):
                phase = "GAP_JOIN"
                st["phase"] = phase
            else:
                blocked = [q["id"] for q in st.get("queue") or [] if q.get("status") == "blocked"]
                halt_program(
                    cwd,
                    "GAP_FANOUT stuck (deps or blocked): " + ",".join(blocked),
                )
                return {
                    "ok": False,
                    "status": "halted",
                    "action": None,
                    "prompt": None,
                    "reason": "fanout stuck",
                }
        else:
            action = _fanout_action(item, phase)

    if phase == "GAP_JOIN" and action is None:
        if not queue_all_done(st.get("queue") or []):
            halt_program(cwd, "GAP_JOIN failed — queue not all done")
            return {
                "ok": False,
                "status": "halted",
                "action": None,
                "prompt": None,
                "reason": "join failed",
            }
        phase = "GAP_CLOSE"
        st["phase"] = phase

    if phase == "GAP_CLOSE" and action is None:
        resume_cmd = (st.get("resume") or {}).get("command") or "INTEG GAP CLOSE"
        action = _action(
            kind="mode",
            phase=phase,
            role="INTEG",
            command=resume_cmd if "GAP CLOSE" in resume_cmd else "INTEG GAP CLOSE",
            artifact=(st.get("resume") or {}).get("implement"),
            reason="journey: GAP CLOSE + rewire",
        )
    elif phase == "INTEG_QA":
        action = _action(
            kind="mode",
            phase=phase,
            role="INTEG",
            command="INTEG QA",
            decompose=st.get("integ_decompose"),
            reason="journey: INTEG QA",
        )
    elif phase == "INTEG_REFLECT":
        action = _action(
            kind="mode",
            phase=phase,
            role="INTEG",
            command="INTEG REFLECT",
            reason="journey: INTEG REFLECT",
        )
    elif phase == "COMPLETE":
        complete_program(cwd, "already complete")
        return {
            "ok": False,
            "status": "complete",
            "action": None,
            "prompt": None,
            "reason": "complete",
        }

    if action is None:
        halt_program(cwd, f"no action for phase={phase}")
        return {
            "ok": False,
            "status": "halted",
            "action": None,
            "prompt": None,
            "reason": f"no action for phase={phase}",
        }

    if action["kind"] == "halt":
        halt_program(cwd, action.get("reason") or "halt action")
        return {
            "ok": False,
            "status": "halted",
            "action": action,
            "prompt": None,
            "reason": action.get("reason"),
        }

    prompt = None
    if action["kind"] == "mode":
        prompt = build_program_prompt(action, cwd, st)
        next_prompt_path(cwd).write_text(prompt + "\n", encoding="utf-8")

    st["current_action"] = action
    st["pending_fingerprint_before"] = el.fingerprint_context(text)
    save_program_state(cwd, st)

    return {
        "ok": True,
        "status": "running",
        "action": action,
        "prompt": prompt,
        "reason": action.get("reason"),
        "phase": st.get("phase"),
        "queue": st.get("queue"),
    }


def _advance_queue_after_mode(st: dict[str, Any], cmd: str | None) -> None:
    action = st.get("current_action") or {}
    gap_id = action.get("gap_id")
    if not gap_id:
        return
    mode = el.command_mode(cmd or action.get("command") or "") if cmd or action.get("command") else None
    queue = st.get("queue") or []
    for it in queue:
        if it["id"] != gap_id:
            continue
        if mode == "PLAN" or (action.get("command") or "").endswith("PLAN"):
            it["status"] = "plan"
            # try capture plan path from handoff load_now later
        elif mode == "DECOMPOSE" or (action.get("command") or "").endswith("DECOMPOSE"):
            it["status"] = "decompose"
        break
    st["queue"] = queue


def _mark_queue_epic_done(st: dict[str, Any], gap_id: str | None) -> None:
    if not gap_id:
        return
    for it in st.get("queue") or []:
        if it["id"] == gap_id:
            it["status"] = "done"
            break


def after_session(cwd: str | Path, *, epic_status: str | None = None) -> dict[str, Any]:
    """Post mode-session or nested epic-loop."""
    st = load_program_state(cwd)
    if not st.get("active"):
        return {"ok": False, "status": st.get("status"), "reason": "not active"}

    text = el.read_active_context(cwd)
    fp = el.fingerprint_context(text)
    before = st.get("pending_fingerprint_before")
    handoff = el.extract_handoff_block(text)
    fields = extract_program_fields(handoff)
    next_cmd = el.parse_next_command(handoff)
    action = st.get("current_action") or {}
    phase = st.get("phase")

    st["iteration"] = int(st.get("iteration") or 0) + 1
    hist = list(st.get("history") or [])
    hist.append(
        {
            "n": st["iteration"],
            "phase": phase,
            "action": action,
            "epic_status": epic_status,
            "fingerprint": fp,
            "at": utc_now(),
        }
    )
    st["history"] = hist[-80:]

    kind = action.get("kind")
    if kind == "mode":
        if before is not None and fp == before:
            halt_program(cwd, "no Handoff/load_now progress after mode session")
            return {
                "ok": False,
                "status": "halted",
                "reason": "no progress (same fingerprint)",
            }
        if el.HALT_RE.search(handoff):
            halt_program(cwd, "human gate after mode session")
            return {"ok": False, "status": "halted", "reason": "human gate"}

        if fields.get("gap"):
            st["gap_path"] = _norm_mb_path(fields["gap"] or "")
        if fields.get("resume"):
            parsed = parse_resume(fields["resume"])
            if parsed:
                st["resume"] = parsed

        # Phase transitions after mode
        if phase == "INTEG_PLAN":
            st["phase"] = "INTEG_DECOMPOSE"
        elif phase == "INTEG_DECOMPOSE":
            # capture decompose from handoff next / load_now
            load = el.extract_load_now(text)
            for p in load:
                if "decompose-" in p:
                    st["integ_decompose"] = el.normalize_decompose_ref(cwd, p)
                    break
            st["phase"] = "INTEG_STEPS"
        elif phase == "GAP_OPEN":
            if st.get("gap_path"):
                st["queue"] = parse_gap_queue(load_gap_file(cwd, st["gap_path"]))
            elif fields.get("gap"):
                gp = _norm_mb_path(fields["gap"] or "")
                st["gap_path"] = gp
                st["queue"] = parse_gap_queue(load_gap_file(cwd, gp))
            st["phase"] = "GAP_FANOUT"
        elif phase == "GAP_FANOUT":
            _advance_queue_after_mode(st, action.get("command"))
            # if PLAN finished, status already plan; try bind plan path from load_now
            load = el.extract_load_now(text)
            gap_id = action.get("gap_id")
            for it in st.get("queue") or []:
                if it["id"] != gap_id:
                    continue
                for p in load:
                    if "plan-" in p and p.endswith(".md"):
                        it["plan"] = p
                    if "decompose-" in p:
                        it["decompose"] = el.normalize_decompose_ref(cwd, p)
            if next_queue_item(st.get("queue") or []) is None and queue_all_done(
                st.get("queue") or []
            ):
                st["phase"] = "GAP_JOIN"
        elif phase == "GAP_CLOSE":
            st["phase"] = "INTEG_RESUME"
        elif phase == "INTEG_QA":
            st["phase"] = "INTEG_REFLECT"
        elif phase == "INTEG_REFLECT":
            save_program_state(cwd, st)
            complete_program(cwd, "INTEG REFLECT done — ARCHIVE вручную")
            return {
                "ok": False,
                "status": "complete",
                "reason": "journey complete after REFLECT",
                "phase": "COMPLETE",
            }

    elif kind == "epic":
        # Nested epic-loop finished
        if epic_status == "halted":
            halt_program(cwd, "nested epic halted")
            return {"ok": False, "status": "halted", "reason": "nested epic halted"}

        if phase in {"INTEG_STEPS", "INTEG_RESUME"}:
            # Epic completed early because next is GAP / ARCHIVE / outside auto
            if next_cmd and el.command_mode(next_cmd) == "GAP":
                st["phase"] = "GAP_OPEN"
            elif next_cmd and el.command_mode(next_cmd) == "ARCHIVE":
                save_program_state(cwd, st)
                complete_program(cwd, "INTEG epic → ARCHIVE")
                return {
                    "ok": False,
                    "status": "complete",
                    "reason": "complete before ARCHIVE",
                    "phase": "COMPLETE",
                }
            elif next_cmd and el.command_mode(next_cmd) in {"QA", "REFLECT"}:
                st["phase"] = "INTEG_QA" if el.command_mode(next_cmd) == "QA" else "INTEG_REFLECT"
            else:
                # pending may remain — if epic complete with no next, go QA
                pending = el.decompose_pending_left(cwd, st.get("integ_decompose"))
                if pending == 0:
                    st["phase"] = "INTEG_QA"
                else:
                    # epic stopped unexpectedly with remaining steps
                    halt_program(cwd, "INTEG epic stopped with pending steps")
                    return {
                        "ok": False,
                        "status": "halted",
                        "reason": "integ epic incomplete",
                    }
        elif phase == "GAP_FANOUT":
            _mark_queue_epic_done(st, action.get("gap_id"))
            if queue_all_done(st.get("queue") or []):
                st["phase"] = "GAP_JOIN"
            else:
                st["phase"] = "GAP_FANOUT"

    if st.get("phase") == "GAP_JOIN" and queue_all_done(st.get("queue") or []):
        st["phase"] = "GAP_CLOSE"

    st["last_fingerprint"] = fp
    st["status"] = "running"
    st["active"] = True
    st["current_action"] = None
    save_program_state(cwd, st)
    return {
        "ok": True,
        "status": "running",
        "reason": "progress ok",
        "phase": st.get("phase"),
        "queue": st.get("queue"),
        "fingerprint": fp,
    }
