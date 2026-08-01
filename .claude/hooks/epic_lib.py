#!/usr/bin/env python3
"""Epic loop state: Handoff → next command (fresh session per step)."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EPIC_DIRNAME = "epic"
EPIC_RESULT_REPAIR_MAX_ATTEMPTS = 3
STATE_NAME = "state.json"
NEXT_PROMPT_NAME = "next-prompt.txt"

ALLOWED_DEFAULT = (
    "IMPLEMENT",
    "CREATIVE",
    "QA",
    "BUGFIX",
    "REFACTOR",
    "SECURITY",
    "REFLECT",
)

_MODE_ALT = (
    r"REFACTOR(?:\s+(?:PLAN|DECOMPOSE))?|"
    r"SECURITY(?:\s+(?:PLAN|DECOMPOSE))?|"
    r"IMPLEMENT|CREATIVE|QA|BUGFIX|REFLECT|ARCHIVE(?:\s+NOW)?|"
    r"TASK|PLAN|DECOMPOSE|VAN|GAP(?:\s+CLOSE)?"
)

CMD_RE = re.compile(
    rf"(?i)\b((?:BACK|FRONT|INTEG)\s+(?:{_MODE_ALT}))\b"
)

HALT_RE = re.compile(
    r"(?i)\b("
    r"grill-?me|needs_human(?:_ok)?|"
    r"останов(?:и|ка)|требуется\s+человек|"
    r"human\s+approval|manual\s+only"
    r")\b"
)

ROLE_MODE_RE = re.compile(
    rf"(?i)^(BACK|FRONT|INTEG)\s+({_MODE_ALT})$"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def epic_dir(cwd: str | Path) -> Path:
    d = Path(cwd) / ".claude" / "runtime" / EPIC_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def state_path(cwd: str | Path) -> Path:
    return epic_dir(cwd) / STATE_NAME


def next_prompt_path(cwd: str | Path) -> Path:
    return epic_dir(cwd) / NEXT_PROMPT_NAME


def default_state() -> dict[str, Any]:
    return {
        "active": False,
        "status": "idle",
        "decompose": None,
        "role_prefix": "BACK",
        "started_at": None,
        "updated_at": None,
        "iteration": 0,
        "max_iterations": 40,
        "halt_reason": None,
        "last_command": None,
        "last_fingerprint": None,
        "allowed_modes": list(ALLOWED_DEFAULT),
        "history": [],
        "model": None,
        "last_verify_verdict": None,
        "last_verify_at": None,
        "pending_implement_step": None,
        "pending_fingerprint_before": None,
    }


def load_epic_state(cwd: str | Path) -> dict[str, Any]:
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


def save_epic_state(cwd: str | Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    from loop_engine import atomic_write_text

    atomic_write_text(
        state_path(cwd),
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
    )


def _sync_loop_ledger(cwd: str | Path, epic_st: dict[str, Any] | None = None) -> None:
    """Dual-source: mirror epic runtime + Handoff into loop/loop-state.yaml."""
    try:
        import loop_engine as le
    except Exception:
        return
    try:
        if epic_st is not None:
            le.sync_from_epic_runtime(cwd, epic_st)
        text = read_active_context(cwd)
        handoff = extract_handoff_block(text)
        load = extract_load_now(text)
        pending = None
        decompose = None
        model = None
        if epic_st:
            decompose = epic_st.get("decompose")
            seed_epic_remaining(cwd, decompose, force=False)
            pending = decompose_pending_left(cwd, decompose)
            model = epic_st.get("model")
        le.sync_from_handoff(
            cwd,
            handoff,
            load_now=load,
            decompose=decompose,
            pending=pending,
            model=model,
            epic_role=(epic_st.get("role_prefix") if epic_st else None),
            save=True,
        )
    except Exception as exc:
        # Do NOT swallow silently: a desync between state.json and loop-state.yaml
        # here is exactly how the ledger ends up pointing at the wrong step.
        # Log to trace.jsonl + stderr so drift is visible; return value unchanged.
        import sys

        try:
            le.append_trace(
                cwd,
                {"kind": "sync_ledger_error", "error": f"{type(exc).__name__}: {exc}"},
                track="epic",
            )
        except Exception:
            pass
        print(
            f"[loop] _sync_loop_ledger FAILED — ledger may drift: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return


def active_context_path(cwd: str | Path) -> Path:
    return Path(cwd) / "memory-bank" / "activeContext.md"


def read_active_context(cwd: str | Path) -> str:
    p = active_context_path(cwd)
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def extract_handoff_block(text: str) -> str:
    m = re.search(r"(?im)^##\s*Handoff\b.*$", text)
    if not m:
        return ""
    start = m.start()
    rest = text[m.end() :]
    nxt = re.search(r"(?im)^##\s+", rest)
    end = m.end() + (nxt.start() if nxt else len(rest))
    return text[start:end].strip()


def _normalize_mb_path(path: str) -> str:
    p = path.strip().lstrip("./")
    if p.startswith(("back/", "front/", "integration/")):
        return f"memory-bank/{p}"
    return p


_INTEG_E_MD = re.compile(r"(?i)/e\d{2}-[a-z0-9-]+\.md$")
_EPIC_S_MD = re.compile(r"(?i)/s\d{2}-[a-z0-9-]+\.md$")


def _coerce_epic_shard_path(path: str) -> str:
    norm = path.replace("\\", "/")
    for pat in (
        r"(?i)((?:s|e|r|a)\d{2}-[a-z0-9-]+)\.md$",
        r"(?i)(qa-\d{8}-[a-z0-9-]+)\.md$",
    ):
        m = re.search(pat, norm)
        if m:
            return f"{norm[: m.start()]}{m.group(1).lower()}.yaml"
    return path


def assert_epic_yaml_shards(paths: list[str]) -> list[str]:
    """Epic shards sNN/eNN — только .yaml/.yml (без md fallback)."""
    for p in paths:
        norm = p.replace("\\", "/")
        if _INTEG_E_MD.search(norm) or _EPIC_S_MD.search(norm):
            raise ValueError(f"Epic shard must be .yaml, not .md: {p}")
    return paths


assert_integ_yaml_shards = assert_epic_yaml_shards


def extract_load_now(text: str) -> list[str]:
    m = re.search(r"(?im)^##\s*load_now\s*$", text)
    if not m:
        return []
    rest = text[m.end() :]
    nxt = re.search(r"(?im)^##\s+", rest)
    body = rest[: nxt.start()] if nxt else rest
    paths: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        p = _coerce_epic_shard_path(_normalize_mb_path(raw))
        if not p or p in seen:
            return
        seen.add(p)
        paths.append(p)

    for line in body.splitlines():
        for pm in re.finditer(
            r"`((?:memory-bank|apps|tests|migrations|back|front|integration)/[^`]+)`",
            line,
        ):
            add(pm.group(1))
        for pm in re.finditer(
            r"\(((?:memory-bank/)?(?:back|front|integration)/[^)\s]+)\)",
            line,
        ):
            add(pm.group(1))
    return paths


def implement_step_from_handoff(handoff: str) -> str | None:
    """Completed IMPLEMENT artifact path from Handoff links (Артефакт / Предыдущий)."""
    for pm in re.finditer(
        r"\(((?:memory-bank/)?(?:back|front|integration)/implement/"
        r"implement-[^)/]+/(?:[se]\d{2}-[^)/]+)\.(?:yaml|yml|md))\)",
        handoff,
    ):
        p = _normalize_mb_path(pm.group(1))
        if p.endswith(".md"):
            return f"{p[:-3]}.yaml"
        return p
    m = re.search(r"(?i)@((?:s|e)\d{2})\b", handoff)
    if m:
        return None  # need epic id — caller uses resolve + basename
    return None


def fingerprint_context(text: str) -> str:
    handoff = extract_handoff_block(text)
    load = "\n".join(extract_load_now(text))
    raw = f"{handoff}\n---\n{load}".strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def validate_active_context_shape(text: str) -> list[str]:
    """Structural hygiene for activeContext.md. Empty list = pass.

    Guards sandwich FINISH: old Handoff/done left under new blocks.
    """
    errors: list[str] = []
    if not (text or "").strip():
        errors.append("activeContext: empty")
        return errors
    handoffs = re.findall(r"(?im)^##\s*Handoff\b", text)
    dones = re.findall(r"(?im)^##\s*done\b", text)
    load_now = re.findall(r"(?im)^##\s*load_now\b", text)
    if len(load_now) != 1:
        errors.append(
            f"activeContext: ожидается ровно 1× ## load_now, найдено {len(load_now)}"
        )
    if len(handoffs) != 1:
        errors.append(
            f"activeContext: ожидается ровно 1× ## Handoff, найдено {len(handoffs)} "
            "(Write весь файл; sandwich/append запрещены)"
        )
    if len(dones) > 1:
        errors.append(
            f"activeContext: ожидается ≤1× ## done, найдено {len(dones)} "
            "(один короткий done; историю — в tasks/log/)"
        )
    return errors


def _normalize_cmd(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).upper().replace("ARCHIVE NOW", "ARCHIVE NOW")


def _role_from_handoff(handoff: str, default: str = "BACK") -> str:
    title = re.search(r"(?im)^##\s*Handoff[^\n]*?\b(BACK|FRONT|INTEG)\b", handoff)
    if title:
        return title.group(1).upper()
    title2 = re.search(r"(?im)^##\s*Handoff\s+(\w+)", handoff)
    role = (title2.group(1).upper() if title2 else default)
    if role not in {"BACK", "FRONT", "INTEG"}:
        return default
    return role


def _cmd_from_line(line: str, handoff: str) -> str | None:
    cm = CMD_RE.search(line)
    if cm:
        return _normalize_cmd(cm.group(1))
    role = _role_from_handoff(handoff)
    if re.search(r"(?i)\ba\d{2}\b|security/", line):
        return f"{role} SECURITY"
    if re.search(r"(?i)\br\d{2}\b|refactor/", line):
        return f"{role} REFACTOR"
    if re.search(r"(?i)\bs\d{2}\b|\be\d{2}\b|implement/", line):
        return f"{role} IMPLEMENT"
    if re.search(r"(?i)creative/", line):
        return f"{role} CREATIVE"
    if re.search(r"(?i)\bqa\b", line):
        return f"{role} QA"
    if re.search(r"(?i)\bbugfix\b", line):
        return f"{role} BUGFIX"
    if re.search(r"(?i)\breflect\b", line):
        return f"{role} REFLECT"
    if re.search(r"(?i)\barchive\b", line):
        return f"{role} ARCHIVE NOW"
    return None


def parse_next_command(handoff: str) -> str | None:
    """Extract next role command from Handoff.

    Prefer explicit **Следующий:** / **Next:**. Fallbacks: Epic QA / title arrow /
    any BACK|FRONT|INTEG <MODE> in the handoff body (last match wins for mode priority).
    """
    for pat in (
        r"(?im)^\s*[-*]\s*\*\*Следующий:\*\*\s*(.+)$",
        r"(?im)^\s*[-*]\s*\*\*Next:\*\*\s*(.+)$",
        r"(?im)^\s*[-*]\s*\*\*Epic QA:\*\*\s*(.+)$",
        r"(?im)^\s*[-*]\s*\*\*Next (?:mode|command):\*\*\s*(.+)$",
    ):
        m = re.search(pat, handoff)
        if m:
            got = _cmd_from_line(m.group(1).strip(), handoff)
            if got:
                return got

    # Title arrow: "## Handoff … → BACK QA …"
    title_line = handoff.splitlines()[0] if handoff.strip() else ""
    arrow = re.search(
        rf"(?i)→\s*((?:BACK|FRONT|INTEG)\s+(?:{_MODE_ALT}))",
        title_line,
    )
    if arrow:
        return _normalize_cmd(arrow.group(1))

    # Any explicit role command in handoff (prefer QA/BUGFIX/REFLECT/ARCHIVE over IMPLEMENT)
    found = [_normalize_cmd(m.group(1)) for m in CMD_RE.finditer(handoff)]
    if not found:
        return None
    priority = {
        "ARCHIVE NOW": 0,
        "ARCHIVE": 0,
        "REFLECT": 1,
        "BUGFIX": 2,
        "QA": 3,
        "CREATIVE": 4,
        "REFACTOR": 5,
        "IMPLEMENT": 6,
    }

    def _prio(cmd: str) -> int:
        mode = command_mode(cmd) or ""
        return priority.get(mode, 50)

    found.sort(key=_prio)
    return found[0]


def command_mode(cmd: str) -> str | None:
    m = ROLE_MODE_RE.match(cmd.strip())
    if not m:
        return None
    return m.group(2).upper().replace("ARCHIVE NOW", "ARCHIVE")


def default_next_after_decompose_done(
    cwd: str | Path,
    *,
    role: str,
    last_command: str | None,
    handoff: str,
) -> str:
    """When all sNN/eNN/rNN/aNN done: QA → BUGFIX↔QA → REFLECT; ARCHIVE stays manual."""
    role = (role or "BACK").upper()
    last_mode = command_mode(last_command) if last_command else None
    parsed = parse_next_command(handoff)
    parsed_mode = command_mode(parsed) if parsed else None

    if parsed_mode in {"QA", "BUGFIX", "REFLECT", "CREATIVE"}:
        return parsed  # type: ignore[return-value]
    if parsed_mode == "ARCHIVE":
        return parsed  # type: ignore[return-value]

    if last_mode == "BUGFIX":
        return f"{role} QA"
    if last_mode == "QA":
        if re.search(r"(?i)—\s*blocked|\bblocked\b|\bFAIL\b", handoff):
            return f"{role} BUGFIX"
        return f"{role} REFLECT"
    if last_mode == "SECURITY" or (last_mode or "").startswith("SECURITY"):
        return f"{role} REFLECT"
    if last_mode == "REFLECT":
        return f"{role} ARCHIVE NOW"
    # last IMPLEMENT/REFACTOR/CREATIVE/None → epic QA
    return f"{role} QA"


def _decompose_index_path(cwd: str | Path, decompose: str | None) -> Path | None:
    if not decompose:
        return None
    root = Path(cwd)
    idx = root / decompose
    if idx.is_dir():
        idx = idx / "index.md"
    if idx.is_file():
        return idx
    if str(decompose).endswith(".md"):
        return None
    for base in (
        root / "memory-bank" / "back" / "plan",
        root / "memory-bank" / "front" / "plan",
        root / "memory-bank" / "integration" / "plan",
        root / "memory-bank" / "back" / "refactor" / "plan",
        root / "memory-bank" / "front" / "refactor" / "plan",
        root / "memory-bank" / "integration" / "refactor" / "plan",
        root / "memory-bank" / "back" / "security" / "plan",
        root / "memory-bank" / "front" / "security" / "plan",
        root / "memory-bank" / "integration" / "security" / "plan",
    ):
        cand = base / decompose / "index.md"
        if cand.is_file():
            return cand
    return None


def is_refactor_decompose(cwd: str | Path, decompose: str | None) -> bool:
    d = str(decompose or "").replace("\\", "/")
    if "/refactor/" in d:
        return True
    idx = _decompose_index_path(cwd, decompose)
    if not idx or not idx.is_file():
        return False
    text = idx.read_text(encoding="utf-8", errors="replace")
    return bool(re.search(r"(?im)\|\s*\*\*r\d{2}\*\*", text)) or bool(
        re.search(r"(?i)\br\d{2}-", text)
    )


def is_security_decompose(cwd: str | Path, decompose: str | None) -> bool:
    d = str(decompose or "").replace("\\", "/")
    if "/security/" in d:
        return True
    idx = _decompose_index_path(cwd, decompose)
    if not idx or not idx.is_file():
        return False
    text = idx.read_text(encoding="utf-8", errors="replace")
    return bool(re.search(r"(?im)\|\s*\*\*a\d{2}\*\*", text)) or bool(
        re.search(r"(?i)\ba\d{2}-", text)
    )


_STEP_STATUS_WORDS = ("pending", "active", "completed", "done", "blocked")


def _row_status_from_body(body: str) -> str | None:
    """Last status token in a table row body (ignore needs_creative yes/no)."""
    words = "|".join(_STEP_STATUS_WORDS)
    status_cell = rf"\**\s*({words})\s*\**"
    found = re.findall(rf"\|\s*{status_cell}\s*\|", body, flags=re.I)
    if found:
        return found[-1].lower()
    m_end = re.search(rf"(?i)\|\s*{status_cell}\s*$", body.rstrip())
    return m_end.group(1).lower() if m_end else None


def _iter_index_step_rows(index_text: str):
    for m in re.finditer(
        r"(?im)^\|\s*\*\*([sera]\d{2})\*\*\s*\|(?P<body>.*)$",
        index_text,
    ):
        body = "|" + m.group("body")
        yield m.group(1).lower(), body, m.group("body")


def _next_phase_from_row(raw_body: str, sid: str) -> str:
    if sid.startswith("a"):
        return "SECURITY"
    if sid.startswith("r"):
        return "REFACTOR"
    if re.search(r"(?i)\bCREATIVE\b", raw_body):
        return "CREATIVE"
    if re.search(r"(?i)\bSECURITY\b", raw_body):
        return "SECURITY"
    if re.search(r"(?i)\bREFACTOR\b", raw_body):
        return "REFACTOR"
    return "IMPLEMENT"


def parse_remaining_from_index(index_text: str) -> list[dict[str, Any]]:
    """Machine queue seed: only pending|active rows from human index view."""
    out: list[dict[str, Any]] = []
    for sid, body, raw in _iter_index_step_rows(index_text):
        st = _row_status_from_body(body)
        if st not in {"pending", "active"}:
            continue
        phase = _next_phase_from_row(raw, sid)
        creative = None
        cms = re.findall(r"\b(CR-[A-Z0-9-]+)\b", raw, flags=re.I)
        if cms and phase == "CREATIVE":
            creative = cms[0].upper()
        item: dict[str, Any] = {"id": sid, "next_phase": phase}
        if creative:
            item["creative"] = creative
        out.append(item)
    return out


def _implement_yaml_completed(cwd: str | Path, role: str, epic_id: str, step_id: str) -> bool:
    try:
        import epic_yaml as ey

        rel = ey.resolve_implement_path(cwd, role, epic_id, step_id.strip().lower())
        return ey.implement_completed(cwd, rel)
    except Exception:
        return False


def reconcile_remaining_with_implement(
    cwd: str | Path, decompose: str | None, remaining: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    epic_id = epic_id_from_decompose_path(decompose or "")
    role = "integ"
    if decompose and "/front/" in str(decompose).replace("\\", "/"):
        role = "front"
    elif decompose and "/back/" in str(decompose).replace("\\", "/"):
        role = "back"
    if not epic_id:
        return remaining
    out: list[dict[str, Any]] = []
    for row in remaining:
        sid = str(row.get("id") or "")
        if _implement_yaml_completed(cwd, role, epic_id, sid):
            continue
        out.append(row)
    return out


def seed_epic_remaining(
    cwd: str | Path,
    decompose: str | None,
    *,
    force: bool = False,
) -> list[dict[str, Any]] | None:
    """Ensure loop-state epic.remaining exists (seed once from index.md)."""
    try:
        import loop_engine as le
    except Exception:
        return None
    st = le.load_loop_state(cwd)
    epic = dict(st.get("epic") or {})
    remaining = epic.get("remaining")
    prev_decompose = epic.get("decompose")
    decompose_changed = bool(
        decompose and prev_decompose and decompose != prev_decompose
    )
    if (
        "remaining" in epic
        and isinstance(remaining, list)
        and not force
        and not decompose_changed
    ):
        epic["pending"] = len(remaining)
        st["epic"] = epic
        le.save_loop_state(cwd, st)
        return remaining
    idx = _decompose_index_path(cwd, decompose or epic.get("decompose"))
    if idx is None or not idx.is_file():
        return remaining if isinstance(remaining, list) else None
    seeded = parse_remaining_from_index(idx.read_text(encoding="utf-8", errors="replace"))
    epic_id = epic_id_from_decompose_path(decompose or epic.get("decompose") or "")
    if epic_id:
        seeded = reconcile_remaining_with_implement(cwd, decompose, seeded)
    epic["remaining"] = seeded
    epic["pending"] = len(seeded)
    if decompose:
        epic["decompose"] = decompose
    st["epic"] = epic
    le.save_loop_state(cwd, st)
    return seeded


def bootstrap_loop_ledger_for_epic(
    cwd: str | Path,
    epic_st: dict[str, Any],
    *,
    from_step: str | None = None,
    force_mode: str | None = None,
) -> dict[str, Any]:
    """On arm / epic switch: re-seed queue + next from decompose (ignore stale Handoff)."""
    try:
        import loop_engine as le
    except Exception:
        return {}

    decompose = epic_st.get("decompose")
    role = (epic_st.get("role_prefix") or "BACK").upper()
    epic_id = epic_id_from_decompose_path(decompose or "")
    seeded = list(seed_epic_remaining(cwd, decompose, force=True) or [])

    if from_step:
        sid = from_step.strip().lower()
        if not re.match(r"^[sera]\d{2}$", sid):
            sid = f"e{sid}" if role == "INTEG" else f"s{sid}"
        cut = next(
            (i for i, row in enumerate(seeded) if str(row.get("id") or "").lower() == sid),
            None,
        )
        if cut is not None:
            seeded = seeded[cut:]

    st = le.load_loop_state(cwd)
    st["role"] = role
    st["active"] = True
    st["status"] = "running"
    st["verdict"] = None
    st["halt_reason"] = None
    st["resume"] = {"command": None, "implement": None, "gap": None}
    st["journey"] = {
        "id": f"INTEG-{epic_id}" if role == "INTEG" else f"{role}-{epic_id}",
        "phase": "EPIC",
    }
    st["epic"] = {
        "decompose": decompose,
        "plan_id": epic_id,
        "remaining": seeded,
        "pending": len(seeded),
    }
    if epic_st.get("model"):
        st["model"] = epic_st["model"]

    if seeded:
        tip = seeded[0]
        phase = (force_mode or str(tip.get("next_phase") or "IMPLEMENT")).upper()
        st["mode"] = phase
        st["next"] = {
            "command": f"{role} {phase}",
            "target": tip.get("creative") or tip.get("id"),
        }
        sid = str(tip.get("id") or "")
        step: dict[str, Any] = {"id": sid, "shard": None, "artifact": None}
        if epic_id and sid:
            try:
                import epic_yaml as ey

                r = (role or "BACK").strip().lower()
                step["shard"] = ey.resolve_decompose_path(cwd, r, epic_id, sid)
                step["artifact"] = ey.resolve_implement_path(cwd, r, epic_id, sid)
                doc = ey.find_implement_doc(cwd, step["artifact"])
                if doc:
                    step["checkpoint"] = doc.resume_from or ey.compute_resume_from(
                        doc.checkpoints
                    )
            except Exception:
                pass
        st["step"] = step
    else:
        st["mode"] = (force_mode or "").upper() or None
        st["next"] = {"command": None, "target": None}
        st["step"] = {"id": None, "shard": None, "artifact": None}

    le.save_loop_state(cwd, st)
    return st


def complete_epic_remaining_step(
    cwd: str | Path, step_id: str | None
) -> list[dict[str, Any]] | None:
    """Pop completed step_id from epic.remaining; pending = len(remaining)."""
    if not step_id:
        return None
    try:
        import loop_engine as le
    except Exception:
        return None
    sid = str(step_id).strip().lower()
    st = le.load_loop_state(cwd)
    epic = dict(st.get("epic") or {})
    remaining = list(epic.get("remaining") or [])
    if not remaining:
        # seed then pop if present
        seeded = seed_epic_remaining(cwd, epic.get("decompose"), force=True)
        st = le.load_loop_state(cwd)
        epic = dict(st.get("epic") or {})
        remaining = list(epic.get("remaining") or [])
        if seeded is None and not remaining:
            return None
    new_rem = [r for r in remaining if str(r.get("id") or "").lower() != sid]
    epic["remaining"] = new_rem
    epic["pending"] = len(new_rem)
    st["epic"] = epic
    # advance cursor tip
    if new_rem:
        tip = new_rem[0]
        step = dict(st.get("step") or {})
        step["id"] = tip.get("id")
        st["step"] = step
        nxt = dict(st.get("next") or {})
        role = (st.get("role") or "BACK").upper()
        phase = str(tip.get("next_phase") or "IMPLEMENT").upper()
        if tip.get("id") and str(tip.get("id")).startswith("r"):
            phase = "REFACTOR"
        nxt["command"] = f"{role} {phase}"
        if tip.get("creative"):
            nxt["target"] = tip["creative"]
        elif tip.get("id"):
            nxt["target"] = tip["id"]
        st["next"] = nxt
        if phase in {"IMPLEMENT", "CREATIVE", "REFACTOR"}:
            st["mode"] = phase
    le.save_loop_state(cwd, st)
    return new_rem


def decompose_pending_left(cwd: str | Path, decompose: str | None) -> int | None:
    """Pending count: prefer loop-state epic.remaining (machine); seed from index if absent."""
    try:
        import loop_engine as le

        st = le.load_loop_state(cwd)
        epic = st.get("epic") or {}
        if "remaining" in epic and isinstance(epic.get("remaining"), list):
            remaining = epic["remaining"]
            n = len(remaining)
            if epic.get("pending") != n:
                epic = dict(epic)
                epic["pending"] = n
                st = dict(st)
                st["epic"] = epic
                le.save_loop_state(cwd, st)
            return n
    except Exception:
        pass
    seeded = seed_epic_remaining(cwd, decompose, force=False)
    if seeded is not None:
        return len(seeded)
    idx = _decompose_index_path(cwd, decompose)
    if idx is None or not idx.is_file():
        return None
    text = idx.read_text(encoding="utf-8", errors="replace")
    return len(parse_remaining_from_index(text))


def normalize_decompose_ref(cwd: str | Path, ref: str) -> str:
    ref = ref.strip().rstrip("/")
    root = Path(cwd).resolve()
    p = Path(ref)
    cand = p if p.is_absolute() else (root / p)
    if cand.is_file():
        try:
            return str(cand.resolve().relative_to(root).as_posix())
        except ValueError:
            return str(cand.as_posix())
    if cand.is_dir() and (cand / "index.md").is_file():
        try:
            return str((cand / "index.md").resolve().relative_to(root).as_posix())
        except ValueError:
            return str((cand / "index.md").as_posix())
    # bare id — feature plan first, then refactor/plan, then security/plan
    for base in (
        root / "memory-bank" / "back" / "plan",
        root / "memory-bank" / "front" / "plan",
        root / "memory-bank" / "integration" / "plan",
        root / "memory-bank" / "back" / "refactor" / "plan",
        root / "memory-bank" / "front" / "refactor" / "plan",
        root / "memory-bank" / "integration" / "refactor" / "plan",
        root / "memory-bank" / "back" / "security" / "plan",
        root / "memory-bank" / "front" / "security" / "plan",
        root / "memory-bank" / "integration" / "security" / "plan",
    ):
        for name in (ref, f"decompose-{ref}", ref.replace("decompose-", "")):
            hit = base / name
            if (hit / "index.md").is_file():
                return str((hit / "index.md").relative_to(root).as_posix())
            if hit.is_file():
                return str(hit.relative_to(root).as_posix())
    return ref


def role_from_decompose_path(decompose: str) -> str | None:
    """Infer BACK|FRONT|INTEG from normalized memory-bank path. None if unknown."""
    p = decompose.replace("\\", "/").lstrip("./")
    markers = (
        ("/integration/", "INTEG"),
        ("memory-bank/integration/", "INTEG"),
        ("/front/", "FRONT"),
        ("memory-bank/front/", "FRONT"),
        ("/back/", "BACK"),
        ("memory-bank/back/", "BACK"),
    )
    for needle, role in markers:
        if needle in p or p.startswith(needle.lstrip("/")):
            return role
    return None


def epic_id_from_decompose_path(decompose: str) -> str:
    raw = (decompose or "").strip()
    if not raw:
        return ""
    path = Path(raw.replace("\\", "/"))
    name = path.parent.name if path.name == "index.md" else path.stem
    if name.startswith("decompose-"):
        return name[len("decompose-") :]
    return name if name not in {".", "..", ""} else ""


def resolve_decompose_arm(
    cwd: str | Path,
    ref: str,
    *,
    role: str | None = None,
    track: str | None = None,
) -> dict[str, str]:
    """Resolve decompose ref → role + track + paths for loop.sh.

    Path under memory-bank/integration/ → role=INTEG, track=program (GAP journey).
    back/ → BACK epic; front/ → FRONT epic.
    Explicit role/track override inference when provided (not AUTO/empty).
    """
    decompose = normalize_decompose_ref(cwd, ref)
    inferred = role_from_decompose_path(decompose)
    role_u = (role or "").strip().upper()
    if not role_u or role_u == "AUTO":
        role_u = inferred or "BACK"
    if role_u not in {"BACK", "FRONT", "INTEG"}:
        raise ValueError(f"unknown role: {role_u}")

    track_l = (track or "").strip().lower()
    if not track_l or track_l == "auto":
        track_l = "program" if role_u == "INTEG" else "epic"
    if track_l not in {"epic", "program"}:
        raise ValueError(f"unknown track: {track_l}")

    epic_id = epic_id_from_decompose_path(decompose)
    out: dict[str, str] = {
        "decompose": decompose,
        "role": role_u,
        "track": track_l,
        "epic_id": epic_id,
        "program_id": f"INTEG-{epic_id}",
        "inferred_role": inferred or "",
    }
    if role_u == "INTEG":
        out["integ_decompose"] = decompose
    return out


def arm_epic(
    cwd: str | Path,
    decompose: str,
    *,
    role_prefix: str | None = None,
    max_iterations: int = 40,
    allowed_modes: list[str] | None = None,
    model: str | None = None,
    from_step: str | None = None,
    force_mode: str | None = None,
) -> dict[str, Any]:
    resolved = resolve_decompose_arm(cwd, decompose, role=role_prefix)
    st = default_state()
    st["active"] = True
    st["status"] = "running"
    st["decompose"] = resolved["decompose"]
    st["role_prefix"] = resolved["role"]
    st["started_at"] = utc_now()
    st["iteration"] = 0
    st["max_iterations"] = max_iterations
    st["halt_reason"] = None
    st["last_command"] = None
    st["last_fingerprint"] = fingerprint_context(read_active_context(cwd))
    st["allowed_modes"] = list(allowed_modes or ALLOWED_DEFAULT)
    st["history"] = []
    if model:
        st["model"] = model.strip()
    save_epic_state(cwd, st)
    bootstrap_loop_ledger_for_epic(
        cwd,
        st,
        from_step=from_step,
        force_mode=force_mode,
    )
    _sync_loop_ledger(cwd, st)
    # Arm hygiene: всегда свежий stub result под текущий epic (не чужой plan/role)
    try:
        from loop_doctor import reset_epic_result_stub

        reset_epic_result_stub(
            cwd,
            role=resolved["role"],
            mode=(force_mode or "IMPLEMENT"),
        )
        import loop_engine as le

        le.append_trace(
            cwd,
            {
                "kind": "arm_result_reset",
                "role": resolved["role"],
                "decompose": resolved["decompose"],
                "plan_id": epic_id_from_decompose_path(resolved["decompose"]),
            },
            track="epic",
        )
    except Exception:
        pass
    return st


def halt_epic(cwd: str | Path, reason: str) -> dict[str, Any]:
    st = load_epic_state(cwd)
    st["active"] = False
    st["status"] = "halted"
    st["halt_reason"] = reason
    save_epic_state(cwd, st)
    _sync_loop_ledger(cwd, st)
    try:
        import loop_engine as le

        le.apply_event(cwd, "human_halt", extra={"halt_reason": reason})
    except Exception:
        pass
    return st


def prepare_result_repair(
    cwd: str | Path,
    reason: str | None = None,
    *,
    max_attempts: int = EPIC_RESULT_REPAIR_MAX_ATTEMPTS,
) -> dict[str, Any]:
    """Re-activate halted epic for one agent repair session (result.yaml / step format)."""
    st = load_epic_state(cwd)
    reason = (reason or st.get("halt_reason") or "result.yaml repair").strip()
    attempts = int(st.get("repair_attempt") or 0)
    if attempts >= max_attempts:
        return {
            "ok": False,
            "status": "halted",
            "reason": f"repair already attempted ({attempts}/{max_attempts}): {reason}",
            "repair_attempt": attempts,
        }
    st["repair_attempt"] = attempts + 1
    st["active"] = True
    st["status"] = "running"
    st["halt_reason"] = reason
    save_epic_state(cwd, st)
    _sync_loop_ledger(cwd, st)

    repair_lines = [
        "RESULT REPAIR (atomic) — исправь ошибку after, затем stop.",
        "",
        "## Repair lanes (HARD — не путать)",
        "1) @verify FAIL/DENY *в сессии* → чини код/step/result → снова @verify "
        "(это НЕ этот prompt).",
        "2) RESULT REPAIR (этот prompt) → только format/docs/`result.yaml` после "
        "`after` FAIL; FORBIDDEN @verify / следующий sNN|eNN.",
        "",
        f"Попытка: {attempts + 1}/{max_attempts}",
        f"Ошибка: {reason}",
        "",
    ]
    pending = st.get("pending_implement_step") or ""
    needs_tests_hint = (
        "implement step format FAIL" in reason
        or "test assert FAIL" in reason
        or "tests:" in reason
    )
    if pending and needs_tests_hint:
        step_path = Path(cwd) / pending
        repair_lines.extend(
            [
                f"Step shard: `{pending}`",
                "",
                "Формат (канон = epic_lib.validate_implement_step_format):",
                *implement_step_format_lines(integ=is_integ_implement_step_path(step_path)),
                "",
                "Проверка после правки (exit 0 = ok):",
                f"python3 .claude/hooks/epic_resolve.py validate-step --path {pending}",
                "",
            ]
        )
    repair_lines.extend(
        [
            "Схема `loop/runtime/epic/result.yaml`:",
            "- status: ok | blocked | fail | halt | gaps  (НЕ pass / pending)",
            "- draft: false",
            "- QA: verdict pass|blocked|fail и status↔verdict "
            "(pass→ok, blocked→blocked, fail→fail)",
            "- artifact: path к qa-*/implement-*/step shard",
            "- Шаблон: `python3 .claude/hooks/loop_resolve.py result --template`",
            "",
            "FORBIDDEN: править loop/loop-state.yaml; @verify; следующий sNN|eNN в этой сессии.",
            "После фикса step shard (+ result.yaml при необходимости) — stop.",
        ]
    )
    prompt = "\n".join(repair_lines)
    path = next_prompt_path(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prompt + "\n", encoding="utf-8")
    try:
        import loop_engine as le

        le.append_trace(
            cwd,
            {
                "kind": "repair",
                "attempt": st["repair_attempt"],
                "reason": reason,
            },
            track="epic",
        )
    except Exception:
        pass
    return {
        "ok": True,
        "status": "running",
        "reason": reason,
        "repair_attempt": st["repair_attempt"],
        "prompt_file": str(path),
    }


def clear_repair_attempt(cwd: str | Path) -> None:
    st = load_epic_state(cwd)
    if st.get("repair_attempt"):
        st["repair_attempt"] = 0
        save_epic_state(cwd, st)


def complete_epic(cwd: str | Path, reason: str = "all steps done") -> dict[str, Any]:
    st = load_epic_state(cwd)
    st["active"] = False
    st["status"] = "complete"
    st["halt_reason"] = reason
    save_epic_state(cwd, st)
    _sync_loop_ledger(cwd, st)
    return st


STEP_BASENAME_RE = re.compile(
    r"(?i)((?:s|e)\d{2}-[a-z0-9][a-z0-9-]*)(?:\.(md|ya?ml))?$"
)
FORBIDDEN_STEP_HEADINGS_RE = re.compile(
    r"(?im)^##\s+("
    r"Реализация(?:\s*/\s*Файлы)?|"
    r"Верификация(?:\s*/\s*Тесты)?|"
    r"Handoff"
    r")\s*$"
)


def extract_step_basename(path: str) -> str | None:
    norm = path.replace("\\", "/").split("/")[-1]
    m = STEP_BASENAME_RE.match(norm)
    if not m:
        return None
    stem = m.group(1).lower()
    ext = (m.group(2) or "").lower()
    if stem.startswith("e") or stem.startswith("s"):
        if ext == "md":
            return f"{stem}.yaml"
        if ext not in {"yaml", "yml", ""}:
            return None
        return f"{stem}.yaml"
    if ext in {"yaml", "yml"}:
        return f"{stem}.{ext}"
    return None


def resolve_expected_implement_step(
    cwd: str | Path,
    load_now: list[str],
    *,
    decompose: str | None,
    role: str,
) -> str | None:
    """Map load_now / decompose → relative path of implement sNN|eNN step artifact.

    Convention: load_now[0] (first step basename) = current atomic work.
    Extra sNN in load_now (peek at next) must not override — first wins, not last.
    """
    role_l = (role or "BACK").strip().lower()
    if role_l == "integ":
        role_dir = "integration"
    elif role_l == "front":
        role_dir = "front"
    else:
        role_dir = "back"

    basename: str | None = None
    for p in load_now:
        norm = p.replace("\\", "/")
        if norm.startswith("memory-bank/"):
            rel = norm
        elif norm.startswith("back/") or norm.startswith("front/") or norm.startswith("integration/"):
            rel = f"memory-bank/{norm}"
        else:
            rel = norm
        bn = extract_step_basename(rel)
        if not bn:
            continue
        if "/implement/" in rel:
            return rel
        basename = bn
        break

    if not basename:
        return None

    epic_id = None
    dec = (decompose or "").replace("\\", "/")
    m = re.search(r"decompose-([^/]+)", dec)
    if m:
        epic_id = m.group(1)
    if not epic_id:
        for p in load_now:
            m = re.search(r"decompose-([^/]+)", p.replace("\\", "/"))
            if m:
                epic_id = m.group(1)
                break
    if not epic_id:
        return None

    import epic_yaml as ey

    stem = Path(basename).stem.lower()
    return ey.resolve_implement_path(cwd, role_l, epic_id, stem)


def is_epic_implement_step_path(path: Path | str) -> bool:
    name = Path(path).name.lower()
    return bool(re.match(r"[se]\d{2}-", name)) and Path(path).suffix.lower() in {
        ".yaml",
        ".yml",
    }


is_integ_implement_step_path = is_epic_implement_step_path


def implement_step_format_lines(*, role: str = "back", integ: bool | None = None) -> list[str]:
    """Human-readable spec for build_prompt / repair (must match validate_implement_step_format)."""
    import epic_yaml as ey

    r = "integ" if integ else role.strip().lower()
    return ey.format_spec_lines(role=r)


def validate_implement_step_format(path: Path) -> list[str]:
    """Strict check: epic-implement/v1 yaml (sNN/eNN — no md)."""
    name = path.name.lower()
    if path.suffix.lower() in {".md"}:
        return [f"Epic implement shard must be .yaml, not .md: {path}"]
    if path.suffix.lower() not in {".yaml", ".yml"}:
        return [f"Epic implement shard must be .yaml: {path}"]
    if not path.is_file():
        return [f"missing implement yaml: {path}"]
    import epic_yaml as ey

    return ey.validate_implement_yaml(path, finish=True)


def decompose_step_status(
    cwd: str | Path, decompose: str | None, step_id: str
) -> str | None:
    """Status from index.md view (diagnostics / seed). Not FINISH gate."""
    idx = _decompose_index_path(cwd, decompose)
    if idx is None or not idx.is_file():
        return None
    sid = step_id.strip().lower()
    text = idx.read_text(encoding="utf-8", errors="replace")
    for row_id, body, _raw in _iter_index_step_rows(text):
        if row_id == sid:
            return _row_status_from_body(body)
    return None


def first_pending_step_next_command(
    cwd: str | Path, decompose: str | None, role: str
) -> str | None:
    """Next command from epic.remaining tip (machine) or index peek."""
    role_u = (role or "BACK").upper()
    try:
        import loop_engine as le

        epic = le.load_loop_state(cwd).get("epic") or {}
        remaining = epic.get("remaining")
        if isinstance(remaining, list) and remaining:
            tip = remaining[0]
            sid = str(tip.get("id") or "")
            phase = str(tip.get("next_phase") or "IMPLEMENT").upper()
            if sid.startswith("a") or phase == "SECURITY":
                return f"{role_u} SECURITY"
            if sid.startswith("r") or phase == "REFACTOR":
                return f"{role_u} REFACTOR"
            if phase == "CREATIVE":
                return f"{role_u} CREATIVE"
            return f"{role_u} IMPLEMENT"
        if isinstance(remaining, list) and not remaining:
            return None
    except Exception:
        pass
    idx = _decompose_index_path(cwd, decompose)
    if idx is None or not idx.is_file():
        return None
    text = idx.read_text(encoding="utf-8", errors="replace")
    for sid, body, raw in _iter_index_step_rows(text):
        st = _row_status_from_body(body)
        if st not in {"pending", "active"}:
            continue
        if sid.startswith("a") or is_security_decompose(cwd, decompose):
            return f"{role_u} SECURITY"
        if sid.startswith("r") or is_refactor_decompose(cwd, decompose):
            return f"{role_u} REFACTOR"
        if re.search(r"(?i)\bCREATIVE\b", raw):
            return f"{role_u} CREATIVE"
        return f"{role_u} IMPLEMENT"
    return None


def command_when_pending_left(
    cwd: str | Path, decompose: str | None, role: str
) -> str:
    """Next auto command while pending>0. Prefer loop-state next; never QA."""
    role_u = (role or "BACK").upper()
    try:
        import loop_engine as le

        ls = le.load_loop_state(cwd)
        nxt = str((ls.get("next") or {}).get("command") or "").strip()
        pending = (ls.get("epic") or {}).get("pending")
        mode = command_mode(nxt) if nxt else None
        mode_base = (mode or "").split()[0] if mode else None
        if (
            pending is not None
            and int(pending) > 0
            and mode_base in {"IMPLEMENT", "CREATIVE", "REFACTOR", "SECURITY"}
        ):
            return nxt
    except Exception:
        pass
    picked = first_pending_step_next_command(cwd, decompose, role_u)
    if picked:
        return picked
    if is_security_decompose(cwd, decompose):
        return f"{role_u} SECURITY"
    if is_refactor_decompose(cwd, decompose):
        return f"{role_u} REFACTOR"
    return f"{role_u} IMPLEMENT"


def handoff_code_changed_no(handoff: str) -> bool:
    return bool(
        re.search(
            r"(?im)(?:\*\*code_changed:\*\*|code_changed:)\s*no\b",
            handoff or "",
        )
    )


def mirror_verify_verdict(cwd: str | Path, verdict: str | None) -> None:
    """Persist verify VERDICT into epic runtime so after_session can read it."""
    if not verdict:
        return
    st = load_epic_state(cwd)
    if not st.get("active"):
        return
    st["last_verify_verdict"] = str(verdict).upper()
    st["last_verify_at"] = utc_now()
    save_epic_state(cwd, st)



# --- split modules (crosscheck + prompt_build) ---
import crosscheck as _crosscheck  # noqa: E402
import prompt_build as _prompt_build  # noqa: E402

_crosscheck.handoff_code_changed_no = handoff_code_changed_no
_crosscheck.parse_next_command = parse_next_command
_crosscheck.command_mode = command_mode
_crosscheck.decompose_pending_left = decompose_pending_left
_crosscheck.validate_implement_step_format = validate_implement_step_format
_crosscheck._decompose_index_path = _decompose_index_path
_crosscheck._normalize_mb_path = _normalize_mb_path
_crosscheck._normalize_mb_path = _normalize_mb_path

_prompt_build.load_epic_state = load_epic_state
_prompt_build.resolve_expected_implement_step = resolve_expected_implement_step
_prompt_build.implement_step_format_lines = implement_step_format_lines
_prompt_build.EPIC_RESULT_REPAIR_MAX_ATTEMPTS = EPIC_RESULT_REPAIR_MAX_ATTEMPTS
_prompt_build.command_mode = command_mode
_prompt_build.is_integ_implement_step_path = is_integ_implement_step_path
_prompt_build.ROLE_MODE_RE = ROLE_MODE_RE
_prompt_build.utc_now = utc_now
_prompt_build._normalize_mb_path = _normalize_mb_path
_prompt_build.extract_step_basename = extract_step_basename
_prompt_build.epic_id_from_decompose_path = epic_id_from_decompose_path

from crosscheck import (  # noqa: E402
    _artifact_from_handoff,
    _pick_mode_artifact,
    validate_qa_shard,
    validate_decompose_step_format,
    validate_refactor_step_format,
    validate_security_step_format,
    validate_creative_shard,
    validate_reflect_shard,
    _crosscheck_qa,
    _crosscheck_creative,
    _crosscheck_reflect,
    crosscheck_ok_result,
    crosscheck_result_artifacts,
)
from prompt_build import (  # noqa: E402
    _pick_allow_read_files,
    _VERIFY_CMD_HINTS,
    _looks_like_verify_cmd,
    _extract_verify_commands,
    _verify_lines_for_mode,
    _role_from_cmd,
    _SPAWN_POINTER,
    _resolve_decompose_for_step,
    _epic_checkpoint_appendix,
    _integ_checkpoint_appendix,
    _mode_appendix,
    build_prompt,
)

def resolve_next(cwd: str | Path) -> dict[str, Any]:
    """Return {ok, status, command, prompt, reason} and update state/files."""
    st = load_epic_state(cwd)
    if not st.get("active") or st.get("status") != "running":
        return {
            "ok": False,
            "status": st.get("status") or "idle",
            "command": None,
            "prompt": None,
            "reason": st.get("halt_reason") or "epic not running",
        }

    if int(st.get("iteration") or 0) >= int(st.get("max_iterations") or 40):
        halt_epic(cwd, f"max_iterations={st.get('max_iterations')}")
        return {
            "ok": False,
            "status": "halted",
            "command": None,
            "prompt": None,
            "reason": "max_iterations reached",
        }

    text = read_active_context(cwd)
    if not text.strip():
        halt_epic(cwd, "activeContext.md missing/empty")
        return {
            "ok": False,
            "status": "halted",
            "command": None,
            "prompt": None,
            "reason": "activeContext missing",
        }

    fp = fingerprint_context(text)
    handoff = extract_handoff_block(text)
    try:
        load_now = assert_integ_yaml_shards(extract_load_now(text))
    except ValueError as exc:
        halt_epic(cwd, str(exc))
        return {
            "ok": False,
            "status": "halted",
            "command": None,
            "prompt": None,
            "reason": str(exc),
        }

    if HALT_RE.search(handoff) or HALT_RE.search(text[:2000]):
        halt_epic(cwd, "human gate in Handoff/context")
        return {
            "ok": False,
            "status": "halted",
            "command": None,
            "prompt": None,
            "reason": "human/grill-me gate",
        }

    # QA blocked → only BUGFIX/QA allowed (None → default_next даст BUGFIX)
    if re.search(r"(?i)Handoff\s+.*\bQA\b", handoff) and re.search(
        r"(?i)—\s*blocked|\bblocked\b", handoff
    ):
        cmd_guess = parse_next_command(handoff) or ""
        mode = command_mode(cmd_guess) if cmd_guess else None
        if mode is not None and mode not in {"BUGFIX", "QA"}:
            halt_epic(cwd, "QA blocked — next must be BUGFIX or QA")
            return {
                "ok": False,
                "status": "halted",
                "command": cmd_guess or None,
                "prompt": None,
                "reason": "QA blocked without BUGFIX/QA next",
            }

    pending = decompose_pending_left(cwd, st.get("decompose"))
    role = st.get("role_prefix") or "BACK"

    # Arm/resolve hygiene: чужой finalized result → clear+stub (fail-fast trace)
    try:
        from loop_doctor import foreign_result_errors, reset_epic_result_stub
        import loop_engine as le

        plan_id = (
            epic_id_from_decompose_path(st["decompose"]) if st.get("decompose") else None
        )
        ferrs = foreign_result_errors(cwd, role=role, plan_id=plan_id, track="epic")
        if ferrs:
            mode_guess = command_mode(st.get("last_command") or "") or "IMPLEMENT"
            reset_epic_result_stub(cwd, role=role, mode=mode_guess)
            le.append_trace(
                cwd,
                {"kind": "foreign_result_reset", "errors": ferrs, "plan_id": plan_id},
                track="epic",
            )
    except Exception:
        pass

    # Ledger sync (Handoff projection) — queue from decompose wins when pending>0
    _sync_loop_ledger(cwd, st)
    pending = decompose_pending_left(cwd, st.get("decompose"))
    ledger_cmd = None
    try:
        import loop_engine as le

        ls = le.load_loop_state(cwd)
        epic_ls = dict(ls.get("epic") or {})
        epic_ls["pending"] = pending
        if st.get("decompose"):
            epic_ls["decompose"] = st.get("decompose")
        ls["epic"] = epic_ls
        mode_ls = (ls.get("mode") or "").upper()
        if pending == 0 and mode_ls in {"IMPLEMENT", "REFACTOR"}:
            preview = le.apply_event(
                cwd,
                "finish_ok",
                state=ls,
                save=True,
            )
            if preview.get("ok"):
                ls = preview["state"]
        else:
            le.save_loop_state(cwd, ls)
        ledger_cmd = le.command_from_state(ls)
        if ls.get("role"):
            role = ls["role"]
    except Exception:
        ledger_cmd = None

    if pending is not None and pending > 0:
        cmd = command_when_pending_left(cwd, st.get("decompose"), role)
    elif ledger_cmd:
        cmd = ledger_cmd
    else:
        cmd = default_next_after_decompose_done(
            cwd,
            role=role,
            last_command=st.get("last_command"),
            handoff=handoff,
        )

    mode = command_mode(cmd)
    if mode is None:
        halt_epic(cwd, f"unparseable command: {cmd}")
        return {
            "ok": False,
            "status": "halted",
            "command": cmd,
            "prompt": None,
            "reason": f"bad command: {cmd}",
        }

    allowed = {m.upper() for m in (st.get("allowed_modes") or ALLOWED_DEFAULT)}
    allowed.add("REFLECT")
    if mode == "ARCHIVE":
        mode_key = "ARCHIVE"
    else:
        mode_key = mode

    # pending>0: never jump to QA/REFLECT/ARCHIVE from bad Handoff/ledger
    if pending is not None and pending > 0 and mode_key in {
        "QA",
        "REFLECT",
        "ARCHIVE",
    }:
        cmd = command_when_pending_left(cwd, st.get("decompose"), role)
        mode = command_mode(cmd)
        mode_key = mode or mode_key

    # pending=0: never re-run IMPLEMENT/REFACTOR — advance to QA/BUGFIX/REFLECT
    if pending == 0 and mode_key in {"IMPLEMENT", "REFACTOR"}:
        cmd = default_next_after_decompose_done(
            cwd,
            role=role,
            last_command=st.get("last_command") or cmd,
            handoff=handoff,
        )
        mode = command_mode(cmd)
        mode_key = "ARCHIVE" if mode == "ARCHIVE" else (mode or mode_key)

    # ARCHIVE NOW — вне автоцикла (ручной). REFLECT — в автоцикле.
    outside_auto = {
        "ARCHIVE",
        "PLAN",
        "DECOMPOSE",
        "VAN",
        "GAP",
        "TASK",
        "REFACTOR PLAN",
        "REFACTOR DECOMPOSE",
    }
    if mode_key in outside_auto:
        complete_epic(cwd, f"next phase outside epic auto: {cmd}")
        return {
            "ok": False,
            "status": "complete",
            "command": cmd,
            "prompt": None,
            "reason": f"epic complete before {cmd} (ARCHIVE/PLAN — вручную)",
        }

    if mode_key not in allowed:
        halt_epic(cwd, f"mode {mode_key} not in allowed_modes")
        return {
            "ok": False,
            "status": "halted",
            "command": cmd,
            "prompt": None,
            "reason": f"mode not allowed: {mode_key}",
        }

    prompt = build_prompt(cmd, cwd, load_now)
    next_prompt_path(cwd).write_text(prompt + "\n", encoding="utf-8")

    st["last_command"] = cmd
    st["pending_fingerprint_before"] = fp
    if mode_key == "IMPLEMENT":
        st["pending_implement_step"] = resolve_expected_implement_step(
            cwd,
            load_now,
            decompose=st.get("decompose"),
            role=role,
        )
    else:
        st["pending_implement_step"] = None
    save_epic_state(cwd, st)
    try:
        import loop_engine as le
        from session_result import write_stub_result

        step_rel = st.get("pending_implement_step")
        step_id = None
        if step_rel:
            m = re.search(r"/([ser]\d{2})-", str(step_rel))
            if m:
                step_id = m.group(1)
        write_stub_result(
            cwd,
            track="epic",
            role=role,
            mode=mode_key,
            step_id=step_id,
            artifact=step_rel,
        )
        ls = le.load_loop_state(cwd)
        role_c, mode_c = le.parse_command(cmd)
        if role_c:
            ls["role"] = role_c
        if mode_c:
            ls["mode"] = mode_c
        nxt = dict(ls.get("next") or {})
        nxt["command"] = cmd
        ls["next"] = nxt
        epic = dict(ls.get("epic") or {})
        epic["pending"] = pending
        if st.get("decompose"):
            epic["decompose"] = st.get("decompose")
        ls["epic"] = epic
        ls["active"] = True
        ls["status"] = "running"
        if st.get("model"):
            ls["model"] = st.get("model")
        le.save_loop_state(cwd, ls)
        st["last_verify_verdict"] = None
        st["last_verify_at"] = None
        save_epic_state(cwd, st)
        le.append_trace(
            cwd,
            {
                "kind": "resolve",
                "command": cmd,
                "mode": mode_key,
                "pending": pending,
                "step": st.get("pending_implement_step"),
                "result_stub": True,
            },
            track="epic",
        )
    except Exception:
        _sync_loop_ledger(cwd, st)

    return {
        "ok": True,
        "status": "running",
        "command": cmd,
        "prompt": prompt,
        "reason": None,
        "fingerprint": fp,
        "load_now": load_now,
        "pending_steps": pending,
        "pending_implement_step": st.get("pending_implement_step"),
        "ledger_command": cmd,
    }



# --- split module (after_session) ---
import after_session as _after_session  # noqa: E402

_after_session.load_epic_state = load_epic_state
_after_session.save_epic_state = save_epic_state
_after_session.read_active_context = read_active_context
_after_session.fingerprint_context = fingerprint_context
_after_session.extract_handoff_block = extract_handoff_block
_after_session.validate_active_context_shape = validate_active_context_shape
_after_session.implement_step_from_handoff = implement_step_from_handoff
_after_session.validate_implement_step_format = validate_implement_step_format
_after_session.command_mode = command_mode
_after_session.decompose_pending_left = decompose_pending_left
_after_session.assert_integ_yaml_shards = assert_integ_yaml_shards
_after_session.extract_load_now = extract_load_now
_after_session.halt_epic = halt_epic
_after_session.complete_epic = complete_epic
_after_session.complete_epic_remaining_step = complete_epic_remaining_step
_after_session.clear_repair_attempt = clear_repair_attempt
_after_session.crosscheck_ok_result = crosscheck_ok_result
_after_session.handoff_code_changed_no = handoff_code_changed_no
_after_session.utc_now = utc_now
_after_session.HALT_RE = HALT_RE
_after_session.epic_id_from_decompose_path = epic_id_from_decompose_path

from after_session import after_session  # noqa: E402


def session_start_payload(cwd: str | Path, source: str | None = None) -> dict[str, Any] | None:
    """If epic running, remind one-step rule (prompt comes from epic-loop -p)."""
    st = load_epic_state(cwd)
    if not st.get("active") or st.get("status") != "running":
        return None
    cmd = st.get("last_command") or "?"
    ctx = (
        f"EPIC MODE on · command≈{cmd} · decompose={st.get('decompose')} · "
        f"source={source or '?'} · iteration={st.get('iteration')}\n"
        "Ровно один atomic шаг → FINISH (Handoff в activeContext) → stop.\n"
        "Не вызывай /clear и не стартуй следующий шаг — это делает loop/epic-loop.sh "
        "(новая сессия = чистый контекст).\n"
        "Prompt уже packed (`next-prompt.txt` / `claude -p`). "
        "Не re-read весь workflow chain — только `activeContext` load_now + ONE shard "
        "+ isolation `_lean/<mode>.mdc` (+ spawn-hard при spawn).\n"
        "VERIFY loop (в сессии, код/step) ≠ RESULT REPAIR (после after, только "
        "docs/result format)."
    )
    out: dict[str, Any] = {
        "additionalContext": ctx,
        "sessionTitle": f"epic:{cmd}",
    }
    # Optional: empty `claude -p` relies on this (epic-loop passes prompt by default).
    if str(__import__("os").environ.get("EPIC_USE_INITIAL_MSG", "")).lower() in {
        "1",
        "true",
        "yes",
    }:
        resolved = resolve_next(cwd)
        if resolved.get("ok") and resolved.get("prompt"):
            out["initialUserMessage"] = resolved["prompt"]
    return out
