#!/usr/bin/env python3
"""Loop engine — declarative transitions + canonical loop-state ledger.

Canon (repo root `loop/` — outside memory-bank):
  loop/loop-state.yaml   — where we are (machine)
  loop/transitions.yaml  — how we move
  memory-bank/activeContext.md — session view (projection)

Epic/program runners call apply_event; they must not invent policy.
"""
from __future__ import annotations

import copy
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

SYSTEM_DIR = "loop"
LOOP_STATE_NAME = "loop-state.yaml"
TRANSITIONS_NAME = "transitions.yaml"

_ROLE_CMD = re.compile(
    r"(?i)\b((?:BACK|FRONT|INTEG)\s+(?:REFACTOR(?:\s+(?:PLAN|DECOMPOSE))?|"
    r"IMPLEMENT|CREATIVE|QA|BUGFIX|REFLECT|ARCHIVE(?:\s+NOW)?|"
    r"TASK|PLAN|DECOMPOSE|VAN|GAP(?:\s+CLOSE)?))\b"
)

_IMPLEMENT_SHARD = re.compile(r"(?i)/(?:[ser]\d{2})-")


def _implement_shard_path(p: str) -> bool:
    norm = p.replace("\\", "/")
    if "/implement/" not in norm or not _IMPLEMENT_SHARD.search(norm):
        return False
    low = norm.lower()
    if low.endswith(".md"):
        return True
    return low.endswith((".yaml", ".yml"))


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def system_dir(cwd: str | Path) -> Path:
    d = Path(cwd) / SYSTEM_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def loop_state_path(cwd: str | Path) -> Path:
    return system_dir(cwd) / LOOP_STATE_NAME


def transitions_path(cwd: str | Path) -> Path:
    return Path(cwd) / SYSTEM_DIR / TRANSITIONS_NAME


def default_loop_state() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": None,
        "active": False,
        "status": "idle",
        "journey": {"id": None, "phase": "EPIC"},
        "role": "BACK",
        "mode": None,
        "epic": {"decompose": None, "plan_id": None, "pending": None},
        "step": {"id": None, "shard": None, "artifact": None},
        "next": {"command": None, "target": None},
        "queue": [],
        "resume": {"command": None, "implement": None, "gap": None},
        "verdict": None,
        "halt_reason": None,
        "model": None,
        "notes": None,
    }


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_loop_state(cwd: str | Path) -> dict[str, Any]:
    p = loop_state_path(cwd)
    st = default_loop_state()
    if not p.is_file():
        return st
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return st
    return _deep_merge(st, data)


def atomic_write_text(path: str | Path, text: str, *, encoding: str = "utf-8") -> None:
    """Crash-safe write: temp file in same dir + fsync + os.replace (atomic rename).

    A direct path.write_text can leave a partial/truncated file if the process
    is killed mid-write; the next load then silently treats it as corrupt/empty
    (silent except) and overwrites real state. Same-dir temp guarantees the
    final os.replace stays on one filesystem.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding=encoding) as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)


def save_loop_state(cwd: str | Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    state["version"] = int(state.get("version") or 1)
    text = yaml.safe_dump(
        state,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    atomic_write_text(loop_state_path(cwd), text)


def load_transitions(cwd: str | Path) -> dict[str, Any]:
    p = transitions_path(cwd)
    if not p.is_file():
        raise FileNotFoundError(f"missing transitions: {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("transitions.yaml must be a mapping")
    return data


def profile_for(cwd: str | Path, role: str) -> dict[str, Any]:
    tr = load_transitions(cwd)
    profiles = tr.get("profiles") or {}
    return dict(profiles.get(role.upper()) or {})


def _when_match(when: dict[str, Any] | None, st: dict[str, Any]) -> bool:
    if not when:
        return True
    role = (st.get("role") or "").upper()
    mode = (st.get("mode") or "").upper().replace("ARCHIVE NOW", "ARCHIVE")
    phase = ((st.get("journey") or {}).get("phase") or "").upper()
    pending = (st.get("epic") or {}).get("pending")
    queue = st.get("queue") or []

    if "role" in when and str(when["role"]).upper() != role:
        return False
    if "mode" in when and str(when["mode"]).upper().replace("ARCHIVE NOW", "ARCHIVE") != mode:
        return False
    if "journey_phase" in when and str(when["journey_phase"]).upper() != phase:
        return False

    if "pending_gt" in when:
        if pending is None:
            return False
        if not (int(pending) > int(when["pending_gt"])):
            return False
    if "pending_eq" in when:
        if pending is None or int(pending) != int(when["pending_eq"]):
            return False

    if "queue_all_done" in when:
        done = (not queue) or all(i.get("status") == "done" for i in queue)
        if bool(when["queue_all_done"]) != done:
            return False

    if "queue_head_role" in when or "queue_head_status" in when:
        head = _queue_head(queue)
        if head is None:
            return False
        if "queue_head_role" in when and head.get("role") != str(when["queue_head_role"]).upper():
            return False
        if "queue_head_status" in when and head.get("status") != when["queue_head_status"]:
            return False

    return True


def _queue_head(queue: list[dict[str, Any]]) -> dict[str, Any] | None:
    by_id = {q["id"]: q for q in queue if q.get("id")}
    for it in queue:
        if it.get("status") in {"done", "blocked"}:
            continue
        ok = True
        for dep in it.get("after") or []:
            other = by_id.get(dep)
            if not other or other.get("status") != "done":
                ok = False
                break
        if ok:
            return it
    return None


def match_transition(
    cwd: str | Path,
    st: dict[str, Any],
    event: str,
) -> dict[str, Any] | None:
    tr = load_transitions(cwd)
    event_u = event.strip().lower()
    for row in tr.get("transitions") or []:
        if str(row.get("on") or "").lower() != event_u:
            continue
        if _when_match(row.get("when") or {}, st):
            return dict(row)
    return None


def apply_then(st: dict[str, Any], then: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(st)
    journey = dict(out.get("journey") or {})
    epic = dict(out.get("epic") or {})
    nxt = dict(out.get("next") or {})
    queue = list(out.get("queue") or [])

    if "role" in then:
        out["role"] = str(then["role"]).upper()
    if "mode" in then:
        out["mode"] = str(then["mode"]).upper().replace("ARCHIVE NOW", "ARCHIVE")
    if "journey_phase" in then:
        journey["phase"] = str(then["journey_phase"]).upper()
    if "verdict" in then:
        out["verdict"] = then["verdict"]
    if then.get("halt"):
        out["active"] = False
        out["status"] = "halted"
        journey["phase"] = "HALT"
    if then.get("complete"):
        out["active"] = False
        out["status"] = "complete"
        journey["phase"] = journey.get("phase") or "COMPLETE"

    if "queue_item_status" in then:
        head = _queue_head(queue)
        if head is not None:
            for it in queue:
                if it.get("id") == head.get("id"):
                    it["status"] = then["queue_item_status"]
                    break

    if then.get("advance_queue"):
        head = _queue_head(queue)
        if head is not None and head.get("status") != "done":
            for it in queue:
                if it.get("id") == head.get("id"):
                    it["status"] = "done"
                    break

    # rebuild next.command from role+mode
    role = out.get("role") or "BACK"
    mode = out.get("mode") or "IMPLEMENT"
    cmd_mode = "ARCHIVE NOW" if mode == "ARCHIVE" else mode
    nxt["command"] = f"{role} {cmd_mode}"
    out["journey"] = journey
    out["epic"] = epic
    out["next"] = nxt
    out["queue"] = queue
    out["active"] = bool(out.get("active")) if out.get("status") == "running" else out.get("active")
    if out.get("status") == "running":
        out["active"] = True
    return out


def apply_event(
    cwd: str | Path,
    event: str,
    *,
    state: dict[str, Any] | None = None,
    save: bool = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply declarative transition. Returns {ok, transition, state, reason}."""
    st = state if state is not None else load_loop_state(cwd)
    if extra:
        st = _deep_merge(st, extra)

    row = match_transition(cwd, st, event)
    if row is None:
        return {
            "ok": False,
            "transition": None,
            "state": st,
            "reason": f"no transition for event={event} role={st.get('role')} mode={st.get('mode')} phase={(st.get('journey') or {}).get('phase')}",
        }

    new_st = apply_then(st, row.get("then") or {})
    # keep running unless halt/complete
    if new_st.get("status") not in {"halted", "complete"}:
        new_st["status"] = "running"
        new_st["active"] = True

    if save:
        save_loop_state(cwd, new_st)
    return {
        "ok": True,
        "transition": row.get("id"),
        "state": new_st,
        "reason": None,
        "then": row.get("then"),
    }


def parse_command(raw: str | None) -> tuple[str | None, str | None]:
    if not raw:
        return None, None
    m = _ROLE_CMD.search(raw)
    if not m:
        return None, None
    parts = re.sub(r"\s+", " ", m.group(1)).upper().split(" ", 1)
    if len(parts) < 2:
        return parts[0], None
    role, mode = parts[0], parts[1]
    mode = mode.replace("ARCHIVE NOW", "ARCHIVE")
    return role, mode


def sync_from_handoff(
    cwd: str | Path,
    handoff: str,
    *,
    load_now: list[str] | None = None,
    decompose: str | None = None,
    pending: int | None = None,
    model: str | None = None,
    journey_id: str | None = None,
    epic_role: str | None = None,
    save: bool = True,
) -> dict[str, Any]:
    """Patch loop-state from Handoff next + optional epic facts (dual-source write)."""
    st = load_loop_state(cwd)
    # next command
    next_line = None
    for pat in (
        r"(?im)^\s*[-*]\s*\*\*Следующий:\*\*\s*(.+)$",
        r"(?im)^\s*[-*]\s*\*\*Next:\*\*\s*(.+)$",
        r"(?im)^\s*[-*]\s*\*\*Epic QA:\*\*\s*(.+)$",
    ):
        m = re.search(pat, handoff)
        if m:
            next_line = m.group(1).strip()
            break

    role, mode = parse_command(next_line or "")
    if not role:
        # title
        tm = re.search(r"(?im)^##\s*Handoff[^\n]*?\b(BACK|FRONT|INTEG)\b", handoff)
        if tm:
            role = tm.group(1).upper()
    epic_role_u = (epic_role or "").strip().upper() or None
    if epic_role_u and role and role != epic_role_u:
        role = epic_role_u
    # pending>0: Handoff QA/REFLECT/ARCHIVE is invalid — keep prior mode / force step chain
    if (
        pending is not None
        and int(pending) > 0
        and mode in {"QA", "REFLECT", "ARCHIVE"}
    ):
        mode = None
    if role:
        st["role"] = role
    if mode:
        st["mode"] = mode

    nxt = dict(st.get("next") or {})
    if role and mode:
        cmd_mode = "ARCHIVE NOW" if mode == "ARCHIVE" else mode
        nxt["command"] = f"{role} {cmd_mode}"
    elif pending is not None and int(pending) > 0:
        poison = (nxt.get("command") or "").upper()
        if mode is None and any(
            tok in poison for tok in (" QA", " REFLECT", " ARCHIVE")
        ):
            nxt.pop("command", None)
        if epic_role_u and poison and not poison.startswith(epic_role_u + " "):
            nxt.pop("command", None)
    # target: prefer CR-* from command; else @target
    if next_line:
        cr = re.search(r"\b(CR-[A-Z0-9-]+)\b", next_line, re.I)
        tm = re.search(r"@\s*([A-Za-z0-9._/-]+)", next_line)
        if cr:
            nxt["target"] = cr.group(1).upper()
        elif tm:
            nxt["target"] = tm.group(1)
    st["next"] = nxt

    # program fields
    gm = re.search(r"(?im)^\s*[-*]\s*\*\*Gap:\*\*\s*`?([^`\n]+)`?", handoff)
    rm = re.search(r"(?im)^\s*[-*]\s*\*\*Resume:\*\*\s*(.+)$", handoff)
    pm = re.search(r"(?im)^\s*[-*]\s*\*\*Program:\*\*\s*(.+)$", handoff)
    resume = dict(st.get("resume") or {})
    if gm:
        resume["gap"] = gm.group(1).strip()
    if rm:
        resume["command"] = rm.group(1).strip()
        impl = re.search(r"@\s*(\S+)", rm.group(1))
        if impl:
            resume["implement"] = impl.group(1).strip("`'\"")
    st["resume"] = resume
    journey = dict(st.get("journey") or {})
    if pm:
        phase = pm.group(1).strip().upper().replace(" ", "_")
        journey["phase"] = phase
    if journey_id:
        journey["id"] = journey_id
    st["journey"] = journey

    epic = dict(st.get("epic") or {})
    if decompose:
        epic["decompose"] = decompose
    if pending is not None:
        epic["pending"] = pending
    st["epic"] = epic

    step = dict(st.get("step") or {})
    if load_now:
        # prefer first non-index shard
        for p in load_now:
            if p.endswith("index.md"):
                continue
            step["shard"] = p
            m = re.search(r"/([ser]\d{2})-", p)
            if m:
                step["id"] = m.group(1)
            break
        for p in load_now:
            if _implement_shard_path(p):
                step["artifact"] = p
                break
    st["step"] = step

    if model:
        st["model"] = model

    # verdict from handoff
    if re.search(r"(?i)—\s*blocked|\bblocked\b", handoff) and mode == "QA":
        st["verdict"] = "blocked"
    elif re.search(r"(?i)—\s*pass|\bpass\b", handoff) and (mode in {None, "REFLECT", "QA"}):
        if "QA" in handoff.upper() and "pass" in handoff.lower():
            st["verdict"] = "pass"

    st["active"] = True
    if mode == "ARCHIVE":
        if pending is not None and int(pending) > 0:
            st["status"] = "running"
            st["active"] = True
            journey = dict(st.get("journey") or {})
            journey["phase"] = "EPIC"
            st["journey"] = journey
        else:
            st["status"] = "complete"
            st["active"] = False
            journey = dict(st.get("journey") or {})
            journey["phase"] = "COMPLETE"
            st["journey"] = journey
    else:
        st["status"] = "running"

    if save:
        save_loop_state(cwd, st)
    return st


def sync_from_epic_runtime(cwd: str | Path, epic_state: dict[str, Any]) -> dict[str, Any]:
    """Mirror .claude/runtime/epic/state.json fields into loop-state (dual-source)."""
    st = load_loop_state(cwd)
    if epic_state.get("decompose"):
        epic = dict(st.get("epic") or {})
        epic["decompose"] = epic_state["decompose"]
        st["epic"] = epic
    if epic_state.get("role_prefix"):
        st["role"] = str(epic_state["role_prefix"]).upper()
    if epic_state.get("model"):
        st["model"] = epic_state["model"]
    if epic_state.get("last_command"):
        role, mode = parse_command(epic_state["last_command"])
        if role:
            st["role"] = role
        if mode:
            st["mode"] = mode
        st["next"] = {
            "command": epic_state["last_command"],
            "target": (st.get("next") or {}).get("target"),
        }
    st["active"] = bool(epic_state.get("active"))
    st["status"] = epic_state.get("status") or st.get("status")
    if epic_state.get("halt_reason"):
        st["halt_reason"] = epic_state["halt_reason"]
    save_loop_state(cwd, st)
    return st


def command_from_state(st: dict[str, Any]) -> str | None:
    nxt = st.get("next") or {}
    if nxt.get("command"):
        return str(nxt["command"])
    role = st.get("role")
    mode = st.get("mode")
    if role and mode:
        cmd_mode = "ARCHIVE NOW" if mode == "ARCHIVE" else mode
        return f"{role} {cmd_mode}"
    return None


def infer_finish_event(
    *,
    result: dict[str, Any],
    last_mode: str | None = None,
    handoff: str = "",
    role: str | None = None,
    pending: int | None = None,
) -> str:
    """Map machine result.yaml → transitions.yaml event. No Handoff fallback."""
    from session_result import event_from_result

    if not result or result.get("_invalid"):
        raise ValueError("result.yaml required (no handoff fallback)")
    return event_from_result(result)


def append_trace(
    cwd: str | Path,
    record: dict[str, Any],
    *,
    track: str = "epic",
) -> Path:
    """Append one JSON line to `.claude/runtime/{track}/trace.jsonl`."""
    import json

    d = Path(cwd) / ".claude" / "runtime" / track
    d.mkdir(parents=True, exist_ok=True)
    path = d / "trace.jsonl"
    row = {"ts": utc_now(), **record}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return path


def validate_transitions_graph(cwd: str | Path) -> dict[str, Any]:
    """Validate transitions.yaml as a graph. Returns {ok, errors, warnings, stats}."""
    tr = load_transitions(cwd)
    errors: list[str] = []
    warnings: list[str] = []
    rows = list(tr.get("transitions") or [])
    if not rows:
        errors.append("no transitions defined")
        return {"ok": False, "errors": errors, "warnings": warnings, "stats": {}}

    ids: list[str] = []
    seen: set[str] = set()
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"transition[{i}] not a mapping")
            continue
        tid = row.get("id")
        if not tid:
            errors.append(f"transition[{i}] missing id")
            continue
        tid = str(tid)
        if tid in seen:
            errors.append(f"duplicate transition id: {tid}")
        seen.add(tid)
        ids.append(tid)
        if "on" not in row:
            errors.append(f"{tid}: missing 'on' event")
        then = row.get("then")
        if then is not None and not isinstance(then, dict):
            errors.append(f"{tid}: 'then' must be a mapping")
        when = row.get("when")
        if when is not None and not isinstance(when, dict):
            errors.append(f"{tid}: 'when' must be a mapping")

    # human_halt must always match empty when
    halt_rows = [r for r in rows if isinstance(r, dict) and r.get("on") == "human_halt"]
    if not halt_rows:
        errors.append("missing human_halt transition")
    elif not any(not (r.get("when") or {}) for r in halt_rows):
        warnings.append("human_halt has no catch-all when: {}")

    profiles = tr.get("profiles") or {}
    auto_modes: set[str] = set()
    for role, prof in profiles.items():
        if not isinstance(prof, dict):
            errors.append(f"profile {role}: not a mapping")
            continue
        for m in prof.get("auto_modes") or []:
            auto_modes.add(str(m).upper().replace("ARCHIVE NOW", "ARCHIVE"))

    # modes that appear as when.mode or then.mode
    when_modes: set[str] = set()
    then_modes: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        when = row.get("when") or {}
        then = row.get("then") or {}
        if isinstance(when, dict) and when.get("mode"):
            when_modes.add(str(when["mode"]).upper().replace("ARCHIVE NOW", "ARCHIVE"))
        if isinstance(then, dict) and then.get("mode"):
            then_modes.add(str(then["mode"]).upper().replace("ARCHIVE NOW", "ARCHIVE"))

    # every auto_mode (except ARCHIVE) should have at least one outgoing finish_* edge
    finish_events = {"finish_ok", "finish_blocked", "finish_fail", "gaps_found"}
    for mode in sorted(auto_modes):
        if mode in {"ARCHIVE"}:
            continue
        outs = [
            r
            for r in rows
            if isinstance(r, dict)
            and (r.get("when") or {}).get("mode")
            and str((r.get("when") or {}).get("mode")).upper().replace("ARCHIVE NOW", "ARCHIVE")
            == mode
            and r.get("on") in finish_events
        ]
        if not outs and mode not in {"GAP", "GAP CLOSE"}:
            # GAP modes use journey_phase when more often
            has_any = any(
                isinstance(r, dict)
                and r.get("on") in finish_events
                and (
                    (
                        (r.get("when") or {}).get("mode")
                        and str((r.get("when") or {})["mode"]).upper().replace("ARCHIVE NOW", "ARCHIVE")
                        == mode
                    )
                    or mode.replace(" ", "")
                    in str((r.get("when") or {}).get("mode") or "").upper().replace(" ", "")
                )
                for r in rows
            )
            if not has_any:
                warnings.append(f"auto_mode {mode}: no finish_* transition with when.mode")

    # then.mode should be known (auto ∪ manual ∪ ARCHIVE)
    known: set[str] = set(auto_modes)
    for role, prof in profiles.items():
        if isinstance(prof, dict):
            for m in prof.get("manual_modes") or []:
                known.add(str(m).upper().replace("ARCHIVE NOW", "ARCHIVE"))
    known.add("ARCHIVE")
    for mode in sorted(then_modes):
        if mode not in known:
            warnings.append(f"then.mode {mode} not in any profile auto/manual")

    stats = {
        "transitions": len(ids),
        "auto_modes": sorted(auto_modes),
        "when_modes": sorted(when_modes),
        "then_modes": sorted(then_modes),
    }
    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
    }


def render_transitions_mermaid(cwd: str | Path) -> str:
    """Render epic-oriented stateDiagram from transitions (mode→mode on finish_*)."""
    tr = load_transitions(cwd)
    lines = ["stateDiagram-v2", "  [*] --> CREATIVE", "  [*] --> IMPLEMENT"]
    seen_edge: set[tuple[str, str, str]] = set()
    for row in tr.get("transitions") or []:
        if not isinstance(row, dict):
            continue
        when = row.get("when") or {}
        then = row.get("then") or {}
        if not isinstance(when, dict) or not isinstance(then, dict):
            continue
        src = when.get("mode")
        dst = then.get("mode")
        if not src or not dst:
            continue
        src_s = str(src).upper().replace("ARCHIVE NOW", "ARCHIVE").replace(" ", "_")
        dst_s = str(dst).upper().replace("ARCHIVE NOW", "ARCHIVE").replace(" ", "_")
        on = str(row.get("on") or "?")
        edge = (src_s, dst_s, on)
        if edge in seen_edge:
            continue
        seen_edge.add(edge)
        label = on
        if when.get("pending_gt") is not None:
            label += " · pending>0"
        if when.get("pending_eq") is not None:
            label += f" · pending={when['pending_eq']}"
        lines.append(f"  {src_s} --> {dst_s}: {label}")
    if any(e[1] == "ARCHIVE" for e in seen_edge):
        lines.append("  ARCHIVE --> [*]")
    return "\n".join(lines) + "\n"


def advance_ledger_after_session(
    cwd: str | Path,
    *,
    last_mode: str | None,
    handoff: str,
    role: str | None,
    pending: int | None,
    decompose: str | None = None,
    load_now: list[str] | None = None,
    model: str | None = None,
    result: dict[str, Any] | None = None,
    track: str = "epic",
) -> dict[str, Any]:
    """Apply transition from required result.yaml. No Handoff event fallback."""
    if not result or result.get("_invalid"):
        reason = "result.yaml missing or invalid (no handoff fallback)"
        append_trace(
            cwd,
            {"kind": "halt", "reason": reason, "result": result},
            track=track,
        )
        return {
            "ok": False,
            "event": None,
            "apply": None,
            "state": load_loop_state(cwd),
            "result_source": None,
            "reason": reason,
        }

    from session_result import validate_result

    verrs = validate_result(result)
    if verrs:
        reason = "result.yaml validate FAIL: " + "; ".join(verrs)
        append_trace(
            cwd,
            {"kind": "halt", "reason": reason, "result": result},
            track=track,
        )
        return {
            "ok": False,
            "event": None,
            "apply": None,
            "state": load_loop_state(cwd),
            "result_source": None,
            "reason": reason,
        }

    st = load_loop_state(cwd)
    from_mode = (last_mode or st.get("mode") or "").upper().replace("ARCHIVE NOW", "ARCHIVE")
    if role:
        st["role"] = role.upper()
    if last_mode:
        st["mode"] = last_mode.upper().replace("ARCHIVE NOW", "ARCHIVE")
    if result.get("mode"):
        st["mode"] = str(result["mode"]).upper().replace("ARCHIVE NOW", "ARCHIVE")
        from_mode = st["mode"]
    if result.get("role"):
        st["role"] = str(result["role"]).upper()
    if result.get("verdict"):
        st["verdict"] = result["verdict"]
    if result.get("step_id"):
        step = dict(st.get("step") or {})
        step["id"] = result["step_id"]
        if result.get("artifact"):
            step["artifact"] = result["artifact"]
        st["step"] = step

    epic = dict(st.get("epic") or {})
    if decompose:
        epic["decompose"] = decompose
    if pending is not None:
        epic["pending"] = pending
    st["epic"] = epic
    if model:
        st["model"] = model
    if load_now:
        step = dict(st.get("step") or {})
        for p in load_now:
            if p.endswith("index.md"):
                continue
            step["shard"] = p
            m = re.search(r"/([ser]\d{2})-", p)
            if m and not step.get("id"):
                step["id"] = m.group(1)
            break
        for p in load_now:
            if _implement_shard_path(p):
                step["artifact"] = step.get("artifact") or p
                break
        st["step"] = step

    event = infer_finish_event(result=result)
    applied = apply_event(cwd, event, state=st, save=True)
    if not applied.get("ok"):
        reason = applied.get("reason") or f"no transition for event={event}"
        append_trace(
            cwd,
            {
                "kind": "halt",
                "reason": reason,
                "event": event,
                "from_mode": from_mode,
                "result": result,
            },
            track=track,
        )
        return {
            "ok": False,
            "event": event,
            "apply": applied,
            "state": load_loop_state(cwd),
            "result_source": "result.yaml",
            "reason": reason,
        }

    st2 = applied["state"]
    nxt = dict(st2.get("next") or {})
    if result.get("target"):
        nxt["target"] = result["target"]
    st2["next"] = nxt
    if result.get("resume_command") or result.get("gap") or result.get("resume_implement"):
        resume = dict(st2.get("resume") or {})
        if result.get("resume_command"):
            resume["command"] = result["resume_command"]
        if result.get("gap"):
            resume["gap"] = result["gap"]
        if result.get("resume_implement"):
            resume["implement"] = result["resume_implement"]
        st2["resume"] = resume
    save_loop_state(cwd, st2)
    applied["state"] = st2

    out_state = load_loop_state(cwd)
    append_trace(
        cwd,
        {
            "kind": "advance",
            "event": event,
            "result_source": "result.yaml",
            "transition": applied.get("transition"),
            "from_mode": from_mode,
            "to_mode": out_state.get("mode"),
            "to_command": command_from_state(out_state),
            "pending": pending,
            "apply_ok": True,
        },
        track=track,
    )
    return {
        "ok": True,
        "event": event,
        "apply": applied,
        "state": out_state,
        "result_source": "result.yaml",
        "reason": None,
    }


def project_load_now(st: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    step = st.get("step") or {}
    epic = st.get("epic") or {}
    resume = st.get("resume") or {}
    for p in (step.get("shard"), step.get("artifact"), epic.get("decompose"), resume.get("gap"), resume.get("implement")):
        if p and p not in paths:
            paths.append(p)
    return paths[:3]


def render_active_context_skeleton(st: dict[str, Any], *, handoff_body: str) -> str:
    """Build minimal activeContext from ledger + provided handoff prose body."""
    load = project_load_now(st)
    lines = ["## load_now"]
    if load:
        for i, p in enumerate(load, start=1):
            rel = p[len("memory-bank/") :] if p.startswith("memory-bank/") else p
            lines.append(f"{i}. [{Path(rel).name}]({rel})")
    else:
        lines.append("1. _(empty — sync loop-state)_")
    lines.append("")
    role = st.get("role") or "BACK"
    mode = st.get("mode") or ""
    lines.append(f"## Handoff {role} {mode}".rstrip())
    lines.append(handoff_body.rstrip())
    lines.append("")
    cmd = command_from_state(st)
    if cmd and "**Следующий:**" not in handoff_body:
        target = (st.get("next") or {}).get("target")
        suffix = f" @{target}" if target else ""
        lines.append(f"- **Следующий:** `{cmd}{suffix}`")
    lines.append("")
    lines.append("## done — do NOT load")
    lines.append("")
    return "\n".join(lines)
