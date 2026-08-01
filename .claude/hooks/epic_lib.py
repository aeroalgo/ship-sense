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
    state_path(cwd).write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
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
    except Exception:
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
    path = Path(decompose.replace("\\", "/"))
    name = path.parent.name if path.name == "index.md" else path.stem
    if name.startswith("decompose-"):
        return name[len("decompose-") :]
    return name or "epic"


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
        f"Попытка: {attempts + 1}/{max_attempts}",
        f"Ошибка: {reason}",
        "",
    ]
    pending = st.get("pending_implement_step") or ""
    if pending and "implement step format FAIL" in reason:
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


def validate_integ_step_format(path: Path) -> list[str]:
    """Validate epic yaml shard — decompose or implement (yaml only)."""
    if path.suffix.lower() in {".md"}:
        return [f"Epic shard must be .yaml, not .md: {path}"]
    if path.suffix.lower() not in {".yaml", ".yml"}:
        return [f"Epic shard must be .yaml: {path}"]
    if not path.is_file():
        return [f"missing epic yaml: {path}"]
    import epic_yaml as ey

    return ey.validate_shard_yaml(path, finish=True)


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


def _artifact_from_handoff(handoff: str, needles: tuple[str, ...]) -> str | None:
    for pm in re.finditer(
        r"\(((?:memory-bank/)?(?:back|front|integration)/[^)\s]+)\)",
        handoff or "",
    ):
        p = _normalize_mb_path(pm.group(1))
        if any(n in p for n in needles):
            return p
    return None


def _pick_mode_artifact(
    result: dict[str, Any],
    handoff: str,
    step_path: str | None,
    needles: tuple[str, ...],
) -> str | None:
    for cand in (result.get("artifact"), step_path):
        if cand and any(n in str(cand) for n in needles):
            return str(cand)
    return _artifact_from_handoff(handoff, needles)


def validate_qa_shard(path: Path, expected_verdict: str) -> list[str]:
    if path.suffix.lower() in {".md"}:
        return [f"Epic QA shard must be .yaml, not .md: {path}"]
    from epic_shard_extra import validate_qa_yaml

    return validate_qa_yaml(path, expected_verdict=expected_verdict)


def validate_decompose_step_format(path: Path) -> list[str]:
    if path.suffix.lower() in {".md"}:
        return [f"Epic decompose shard must be .yaml, not .md: {path}"]
    if path.suffix.lower() not in {".yaml", ".yml"}:
        return [f"Epic decompose shard must be .yaml: {path}"]
    import epic_yaml as ey

    return ey.validate_decompose_yaml(path)


def validate_refactor_step_format(path: Path) -> list[str]:
    if path.suffix.lower() in {".md"}:
        return [f"Epic refactor shard must be .yaml, not .md: {path}"]
    if path.suffix.lower() not in {".yaml", ".yml"}:
        return [f"Epic refactor shard must be .yaml: {path}"]
    from epic_shard_extra import validate_refactor_yaml

    return validate_refactor_yaml(path, finish=True)


def validate_security_step_format(path: Path) -> list[str]:
    if path.suffix.lower() in {".md"}:
        return [f"Epic security shard must be .yaml, not .md: {path}"]
    if path.suffix.lower() not in {".yaml", ".yml"}:
        return [f"Epic security shard must be .yaml: {path}"]
    from epic_shard_extra import validate_security_yaml

    return validate_security_yaml(path, finish=True)


def _validate_qa_shard_md_legacy(path: Path, expected_verdict: str) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing qa shard: {path}"]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"unreadable qa shard: {path} ({exc})"]

    vm = re.search(r"(?im)^\*\*Verdict:\*\*\s*(\w+)\s*$", text)
    if not vm:
        errors.append("qa shard missing **Verdict:** pass|fail|blocked")
    else:
        got = vm.group(1).strip().lower()
        exp = expected_verdict.strip().lower()
        if got != exp:
            errors.append(f"qa **Verdict:** {got!r} ≠ result.verdict={exp!r}")

    if not re.search(r"(?im)^##\s*Checks\b", text):
        errors.append("qa missing ## Checks")
    if not re.search(r"(?im)^##\s*Scope\b", text):
        errors.append("qa missing ## Scope")

    if expected_verdict.strip().lower() in {"fail", "blocked"}:
        if not re.search(r"(?im)^##\s*Fix plan\b", text):
            errors.append("qa fail/blocked requires ## Fix plan")

    return errors


def validate_creative_shard(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing creative shard: {path}"]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"unreadable creative shard: {path} ({exc})"]

    if not re.search(r"(?im)creative-", path.name) and "CREATIVE" not in text[:200].upper():
        errors.append("creative path/title must look like creative-*.md / CREATIVE")

    sm = re.search(r"(?im)^\*\*Статус:\*\*\s*(.+)$", text)
    if not sm or "closed" not in sm.group(1).lower():
        errors.append("creative **Статус:** must be closed")

    if not re.search(r"(?im)(\*\*Creative ID:\*\*\s*CR-[A-Z0-9-]+|\bCR-[A-Z0-9-]{2,}\b)", text):
        errors.append("creative missing Creative ID / CR-*")

    if not re.search(r"(?im)^##\s*Skills gate\b", text):
        errors.append("creative missing ## Skills gate")

    return errors


def validate_reflect_shard(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing reflection shard: {path}"]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"unreadable reflection shard: {path} ({exc})"]

    if "REFLECT" not in text[:120].upper() and not path.name.startswith("reflection-"):
        errors.append("reflection title/path must be reflection-* / REFLECT")

    sm = re.search(r"(?im)^\*\*Статус:\*\*\s*(.+)$", text)
    if not sm or "completed" not in sm.group(1).lower():
        errors.append("reflection **Статус:** must be completed")

    for sec in ("## Сравнение", "## Что сработало", "## Уроки"):
        if not re.search(rf"(?im)^{re.escape(sec)}\b", text):
            errors.append(f"reflection missing {sec}")

    return errors


def _crosscheck_qa(
    cwd: str | Path,
    result: dict[str, Any],
    *,
    handoff: str,
    step_path: str | None,
) -> list[str]:
    errors: list[str] = []
    status = str(result.get("status") or "")
    verdict = result.get("verdict")
    if not verdict or str(verdict).lower() not in {"pass", "blocked", "fail"}:
        errors.append("QA result requires verdict: pass|blocked|fail")
        return errors

    v = str(verdict).lower()
    expected_status = {"pass": "ok", "blocked": "blocked", "fail": "fail"}[v]
    if status != expected_status:
        errors.append(
            f"QA status={status!r} несовместим с verdict={v!r} (ожидали {expected_status})"
        )

    art = _pick_mode_artifact(result, handoff, step_path, ("/qa/",))
    if not art:
        errors.append("QA: нет qa-shard path (result.artifact / Handoff Артефакт)")
    else:
        errors.extend(validate_qa_shard(Path(cwd) / art, v))

    return errors


def _crosscheck_creative(
    cwd: str | Path,
    result: dict[str, Any],
    *,
    handoff: str,
    step_path: str | None,
    decompose: str | None,
) -> list[str]:
    errors: list[str] = []
    art = _pick_mode_artifact(result, handoff, step_path, ("/creative/",))
    if not art:
        errors.append("CREATIVE: нет creative path (result.artifact / Handoff)")
        return errors

    path = Path(cwd) / art
    errors.extend(validate_creative_shard(path))

    cr = None
    if path.is_file():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            text = ""
        m = re.search(r"(?im)\*\*Creative ID:\*\*\s*(CR-[A-Z0-9-]+)", text)
        if m:
            cr = m.group(1).upper()
        else:
            m2 = re.search(r"\b(CR-[A-Z0-9-]{2,})\b", text)
            if m2:
                cr = m2.group(1).upper()

    if cr and decompose:
        idx = _decompose_index_path(cwd, decompose)
        if idx and idx.is_file():
            open_steps: list[str] = []
            for step in sorted(idx.parent.glob("s*.md")):
                st_text = step.read_text(encoding="utf-8", errors="replace")
                if cr not in st_text.upper():
                    continue
                for line in st_text.splitlines()[:12]:
                    if not re.search(r"(?im)needs_creative:", line):
                        continue
                    if re.search(r"(?im)needs_creative:\s*yes", line) and not re.search(
                        r"(?i)closed", line
                    ):
                        open_steps.append(step.name)
            if open_steps:
                errors.append(
                    f"CREATIVE gate: {cr} ещё open в {', '.join(open_steps)} "
                    "(needs_creative … — **closed**)"
                )

    if not re.search(r"(?i)IMPLEMENT", handoff or ""):
        errors.append("CREATIVE Handoff: ожидается Следующий … IMPLEMENT")

    return errors


def _crosscheck_reflect(
    cwd: str | Path,
    result: dict[str, Any],
    *,
    handoff: str,
    step_path: str | None,
) -> list[str]:
    errors: list[str] = []
    art = _pick_mode_artifact(result, handoff, step_path, ("/reflection/",))
    if not art:
        errors.append("REFLECT: нет reflection path (result.artifact / Handoff)")
        return errors
    errors.extend(validate_reflect_shard(Path(cwd) / art))
    if not re.search(r"(?i)ARCHIVE\s+NOW", handoff or ""):
        errors.append("REFLECT Handoff: обязателен Следующий … ARCHIVE NOW")
    return errors


def crosscheck_ok_result(
    cwd: str | Path,
    result: dict[str, Any],
    *,
    last_mode: str | None,
    decompose: str | None,
    step_path: str | None,
    handoff: str,
    verify_verdict: str | None,
) -> list[str]:
    """Mechanical asserts by mode. Empty list = pass.

    QA: any finalized status (ok/blocked/fail) + verdict ↔ qa-shard.
    CREATIVE/REFLECT/IMPLEMENT: primarily status=ok contracts.
    """
    return crosscheck_result_artifacts(
        cwd,
        result,
        last_mode=last_mode,
        decompose=decompose,
        step_path=step_path,
        handoff=handoff,
        verify_verdict=verify_verdict,
    )


def crosscheck_result_artifacts(
    cwd: str | Path,
    result: dict[str, Any],
    *,
    last_mode: str | None,
    decompose: str | None,
    step_path: str | None,
    handoff: str,
    verify_verdict: str | None,
) -> list[str]:
    status = str(result.get("status") or "")
    mode = str(result.get("mode") or last_mode or "").upper().replace(
        "ARCHIVE NOW", "ARCHIVE"
    )
    errors: list[str] = []

    if mode == "QA":
        return _crosscheck_qa(
            cwd, result, handoff=handoff, step_path=step_path
        )

    if mode == "CREATIVE":
        if status != "ok":
            return []
        return _crosscheck_creative(
            cwd,
            result,
            handoff=handoff,
            step_path=step_path,
            decompose=decompose,
        )

    if mode == "REFLECT":
        if status != "ok":
            return []
        return _crosscheck_reflect(
            cwd, result, handoff=handoff, step_path=step_path
        )

    if mode == "DECOMPOSE":
        if status != "ok":
            return []
        if not step_path:
            errors.append("status=ok DECOMPOSE: нет decompose shard path")
        else:
            errors.extend(validate_decompose_step_format(Path(cwd) / step_path))
        if not result.get("step_id"):
            errors.append("status=ok DECOMPOSE: нет result.step_id")
        return errors

    if status != "ok":
        return []

    if mode == "REFACTOR":
        if not step_path:
            errors.append("status=ok REFACTOR: нет step artifact path")
        else:
            errors.extend(validate_refactor_step_format(Path(cwd) / step_path))
        if not result.get("step_id"):
            errors.append("status=ok REFACTOR: нет result.step_id")
        # fall through to pending/verify checks below

    elif mode == "SECURITY" or mode.startswith("SECURITY"):
        if not step_path:
            errors.append("status=ok SECURITY: нет aNN artifact path")
        else:
            errors.extend(validate_security_step_format(Path(cwd) / step_path))
        if not result.get("step_id"):
            errors.append("status=ok SECURITY: нет result.step_id")
        if handoff_code_changed_no(handoff):
            return errors
        return errors

    elif mode == "IMPLEMENT":
        if not step_path:
            errors.append("status=ok IMPLEMENT: нет step artifact path")
        else:
            errors.extend(validate_implement_step_format(Path(cwd) / step_path))
        if not result.get("step_id"):
            errors.append("status=ok IMPLEMENT: нет result.step_id")
        # Step done = result.yaml ok + artifact. index.md is human view only.
        # Machine cursor: loop/loop-state.yaml (advanced on after).

    # Epic still has steps → Handoff must not jump to QA
    if decompose and mode in {"IMPLEMENT", "REFACTOR", "CREATIVE", "BUGFIX"}:
        pending = None
        try:
            import loop_engine as le

            p = (le.load_loop_state(cwd).get("epic") or {}).get("pending")
            if p is not None:
                pending = int(p)
        except Exception:
            pending = None
        if pending is None:
            pending = decompose_pending_left(cwd, decompose)
        if pending is not None and pending > 0:
            next_cmd = parse_next_command(handoff)
            next_mode = command_mode(next_cmd) if next_cmd else None
            if next_mode == "QA" or (
                next_cmd is None
                and re.search(r"(?im)^\s*[-*]\s*\*\*Epic QA:\*\*", handoff or "")
            ):
                errors.append(
                    f"status=ok: Handoff next=QA при pending={pending} "
                    "в decompose — QA запрещён, пока есть шаги эпика"
                )

    if mode in {"IMPLEMENT", "REFACTOR", "BUGFIX"}:
        if handoff_code_changed_no(handoff):
            return errors
        vv = (verify_verdict or "").upper() or None
        if vv == "FAIL":
            errors.append("status=ok несовместим с verify VERDICT: FAIL")
        elif vv != "PASS":
            errors.append(
                "status=ok требует verify VERDICT: PASS "
                f"(got {vv!r}; code_changed≠no)"
            )

    return errors


def _pick_allow_read_files(load_now: list[str], cmd: str) -> list[str]:
    """≤10 concrete files for reviewer/verify ALLOW READ (no dirs, no globs)."""
    root_candidates: list[str] = []
    seen: set[str] = set()

    def add(p: str) -> None:
        p = p.strip()
        if not p or p in seen:
            return
        if p.endswith("/") or "**" in p:
            return
        seen.add(p)
        root_candidates.append(p)

    for p in load_now:
        if "qa/" in p or "bugfix/" in p or "implement/" in p or "refactor/" in p:
            add(p)
    for p in load_now:
        add(p)
    for p in (
        "memory-bank/activeContext.md",
        "docker-compose.yml",
        "pyproject.toml",
        "apps/edge/storage/writer.py",
        "tests/storage/test_storage_contracts.py",
    ):
        add(p)
    return root_candidates[:10]


def _extract_verify_commands(cwd: str | Path, load_now: list[str]) -> list[str]:
    """Collect exact pytest commands from current step/qa shard for packed prompts."""
    root = Path(cwd)
    commands: list[str] = []
    seen: set[str] = set()

    def add(cmd: str) -> None:
        cmd = cmd.strip()
        if cmd.startswith("- "):
            cmd = cmd[2:].strip()
        if cmd.startswith("`") and cmd.endswith("`"):
            cmd = cmd[1:-1].strip()
        if not cmd.startswith(".venv/bin/pytest ") or cmd in seen:
            return
        seen.add(cmd)
        commands.append(cmd)

    prioritized = sorted(
        load_now,
        key=lambda p: (
            0 if re.search(r"/[ser]\d{2}-.*\.md$", p) else 1,
            0 if "qa/" in p else 1,
            p,
        ),
    )
    for rel_path in prioritized:
        if not rel_path.endswith((".md", ".yaml", ".yml")):
            continue
        path = root / rel_path
        if not path.is_file():
            continue
        if path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml as _yaml

                data = _yaml.safe_load(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for key in ("tests", "verification_results", "verify"):
                        for item in data.get(key) or []:
                            if isinstance(item, str) and ".venv/bin/pytest " in item:
                                add(item)
                    if commands:
                        break
            except Exception:
                pass
            continue
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                if ".venv/bin/pytest " not in raw:
                    continue
                line = raw.strip()
                if "`" in line:
                    for part in re.findall(r"`([^`]+)`", line):
                        add(part)
                else:
                    add(line)
        except Exception:
            continue
        if commands:
            break
    return commands[:3]


def _role_from_cmd(cmd: str) -> str:
    m = ROLE_MODE_RE.match(cmd.strip())
    return m.group(1).upper() if m else "BACK"


_SPAWN_POINTER = (
    "Spawn packed (explorer/verify/reviewer): `.claude/instructions/spawn-hard.md` "
    "+ UserPromptSubmit SPAWN_MAP — не дублировать секции AC+/ALLOW здесь."
)


def _epic_checkpoint_appendix(
    cwd: str | Path, load_now: list[str], role: str
) -> list[str]:
    try:
        import epic_yaml as ey

        st = load_epic_state(cwd)
        role_l = (role or "BACK").strip().lower()
        step_rel = resolve_expected_implement_step(
            cwd,
            load_now,
            decompose=st.get("decompose"),
            role=role.upper(),
        )
        if not step_rel:
            return []
        doc = ey.find_implement_doc(cwd, step_rel)
        if doc:
            return ey.checkpoint_prompt_lines(doc)
        dec_stem = Path(step_rel).stem
        epic_id = epic_id_from_decompose_path(st.get("decompose") or "")
        if not epic_id:
            return []
        sid_m = re.match(r"^([se]\d{2})", dec_stem.lower())
        step_key = sid_m.group(1) if sid_m else dec_stem.lower()
        dec_rel = ey.resolve_decompose_path(cwd, role_l, epic_id, step_key)
        dec_p = Path(cwd) / dec_rel
        if not dec_p.is_file():
            return []
        dec = ey.load_decompose(dec_p)
        impl_p = Path(cwd) / step_rel
        impl_p.parent.mkdir(parents=True, exist_ok=True)
        seeded = ey.seed_implement_checkpoints(dec, None)
        role_dir = ey.role_dir(role_l)
        data: dict[str, Any] = {
            "schema": ey.SCHEMA_EPIC_IMPLEMENT,
            "role": role_l,
            "step_id": dec.step_id,
            "plan_id": dec.plan_id,
            "title": dec.title,
            "status": "in_progress",
            "decompose_ref": dec_rel,
            "implement_index": f"memory-bank/{role_dir}/implement/implement-{epic_id}/index.md",
            "date": "2026-08-01",
            "checkpoints": [c.model_dump() for c in seeded],
            "resume_from": ey.compute_resume_from(seeded),
        }
        if role_l == "integ":
            data["element_ref"] = dec_rel
            data["gaps"] = {"status": "none"}
            data["grep_control"] = [r.model_dump() for r in dec.grep_control]
            data["verification_results"] = []
        else:
            data["done"] = []
            data["files"] = []
            data["tests"] = []
            data["integration_check"] = []
        import yaml as _yaml

        impl_p.write_text(
            _yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        doc = ey.load_implement(impl_p)
        return ey.checkpoint_prompt_lines(doc)
    except Exception:
        pass
    return []


_integ_checkpoint_appendix = _epic_checkpoint_appendix


def _mode_appendix(cmd: str, cwd: str | Path, load_now: list[str]) -> list[str]:
    mode = command_mode(cmd) or ""
    role = _role_from_cmd(cmd)

    if mode == "QA":
        return [
            "",
            f"## {role} QA (HARD)",
            *(__import__("epic_shard_extra", fromlist=["qa_format_spec_lines"]).qa_format_spec_lines(role=role.strip().lower())),
            "Parent suite → @reviewer packed → FINISH qa-*.yaml + один Handoff.",
            "result.yaml: verdict pass|blocked|fail; status↔verdict; draft=false.",
            "Next-mode: `loop/transitions.yaml` (не invent).",
            _SPAWN_POINTER,
        ]

    if mode == "DECOMPOSE":
        role_l = role.strip().lower()
        return [
            "",
            "## path-rule DECOMPOSE step (HARD)",
            *(__import__("epic_shard_extra", fromlist=["decompose_format_spec_lines"]).decompose_format_spec_lines(role=role_l)),
            "FINISH artifact: decompose shard `.yaml` only (не index).",
            _SPAWN_POINTER,
        ]

    if mode == "IMPLEMENT":
        verify_cmds = _extract_verify_commands(cwd, load_now)
        verify_lines = verify_cmds or [".venv/bin/pytest <targeted-test-from-step-shard> -q"]
        integ = role == "INTEG"
        role_l = role.strip().lower()
        extra = _epic_checkpoint_appendix(cwd, load_now, role)
        artifact_hint: list[str] = []
        st = load_epic_state(cwd)
        step_rel = resolve_expected_implement_step(
            cwd,
            load_now,
            decompose=st.get("decompose"),
            role=role,
        )
        if step_rel:
            artifact_hint = [
                f"result.yaml artifact ({role}): `{step_rel}` — только .yaml, не .md",
            ]
        return [
            "",
            "## path-rule IMPLEMENT step (HARD)",
            *implement_step_format_lines(role=role_l, integ=integ),
            *artifact_hint,
            *extra,
            "Канон: finish-block.mdc · validator = loop after-hook "
            f"(до {EPIC_RESULT_REPAIR_MAX_ATTEMPTS}× RESULT REPAIR при FAIL).",
            "",
            "## spawn (pointer)",
            "code_changed=yes → @verify; codebase search → @explorer.",
            "VERIFY cmds (вставить в packed VERIFY:):",
            *[f"- {line}" for line in verify_lines],
            _SPAWN_POINTER,
        ]

    if mode == "REFACTOR":
        verify_cmds = _extract_verify_commands(cwd, load_now)
        verify_lines = verify_cmds or [".venv/bin/pytest <targeted-test-from-rNN-shard> -q"]
        role_l = role.strip().lower()
        return [
            "",
            "## path-rule REFACTOR epic (HARD)",
            *(__import__("epic_shard_extra", fromlist=["refactor_format_spec_lines"]).refactor_format_spec_lines(role=role_l)),
            "`memory-bank/{role}/refactor/implement/implement-<id>/rNN-<slug>.yaml`",
            "FORBIDDEN: session-*.md в корне refactor/ при эпике; legacy `.md` rNN shard.",
            "Behavior freeze; один rNN за сессию. Канон: workflow-refactor-epic.mdc",
            "",
            "## spawn (pointer)",
            "code_changed=yes → @verify.",
            "VERIFY cmds:",
            *[f"- {line}" for line in verify_lines],
            _SPAWN_POINTER,
        ]

    if mode == "SECURITY" or (mode or "").startswith("SECURITY"):
        role_l = role.strip().lower()
        return [
            "",
            "## path-rule SECURITY epic (HARD)",
            *(__import__("epic_shard_extra", fromlist=["security_format_spec_lines"]).security_format_spec_lines(role=role_l)),
            "Submode: PLAN | DECOMPOSE | execute — detect из args / load_now.",
            "`memory-bank/{role}/security/implement/implement-<id>/aNN-<slug>.yaml`",
            "S one-shot: `security/security-audit-YYYYMMDD-<slug>.md` (без yaml).",
            "FORBIDDEN: root-audit + implement/aNN одновременно; не чинить код.",
            "code_changed: no. Канон: workflow-security-epic.mdc",
            _SPAWN_POINTER,
        ]

    if mode == "BUGFIX":
        verify_cmds = _extract_verify_commands(cwd, load_now)
        verify_lines = verify_cmds or [".venv/bin/pytest <targeted-test-from-bugfix-shard> -q"]
        return [
            "",
            "## BUGFIX (HARD)",
            "Root-cause fix (без fallback/hide) → targeted pytest → @verify если code_changed.",
            "VERIFY cmds:",
            *[f"- {line}" for line in verify_lines],
            "Next-mode: `loop/transitions.yaml` (обычно → QA).",
            _SPAWN_POINTER,
        ]

    if mode == "CREATIVE":
        return [
            "",
            "## CREATIVE (HARD)",
            "Skills gate: Core ∪ situational ≤5 в ## Skills gate.",
            "result.yaml ok + creative **Статус:** closed + CR-* .",
            "Rewire sNN needs_creative → closed. Next: transitions → IMPLEMENT.",
        ]

    if mode == "REFLECT":
        return [
            "",
            "## REFLECT (HARD)",
            "result.yaml ok + reflection **Статус:** completed (Сравнение/Что сработало/Уроки).",
            f"Handoff `- **Следующий:** {role} ARCHIVE NOW` — loop complete; ARCHIVE вручную.",
            "FORBIDDEN: ARCHIVE NOW / mb-archive в этой сессии.",
        ]

    return []


def build_prompt(cmd: str, cwd: str | Path, load_now: list[str]) -> str:
    lines = [
        cmd,
        "",
        "EPIC MODE: один atomic шаг. FINISH → Write весь activeContext.md целиком "
        "(load_now → ровно 1× ## Handoff → ≤1× ## done) + stop.",
        "result.yaml: Write implement step on disk → finalize (draft=false, "
        "artifact=implement path) → @verify → "
        "FAIL/DENY: fix blockers/prompt → снова @verify → PASS → FINISH.",
        "FORBIDDEN: @verify после VERDICT: PASS; править loop/loop-state.yaml; "
        "стопка Handoff; sandwich (старый Handoff/done в хвосте); completed в load_now; "
        "следующий sNN в этой сессии; /exit|/clear.",
        "Перед FINISH: 1× re-read activeContext ИЛИ Write целиком (не partial Edit).",
        "Next-mode: loop/transitions.yaml. Spawn: spawn-hard.md + SPAWN_MAP (hook).",
        "Старт:",
        "1. memory-bank/activeContext.md → load_now + §Handoff",
    ]
    if load_now:
        lines.append(f"2. {load_now[0]}")
        for i, p in enumerate(load_now[1:3], start=3):
            lines.append(f"{i}. {p}")
    else:
        lines.append("2. shard из Handoff / decompose index (первый pending/active)")
    lines.extend(_mode_appendix(cmd, cwd, load_now))
    return "\n".join(lines)


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


def after_session(cwd: str | Path) -> dict[str, Any]:
    """Call after claude -p exits: detect progress or halt."""
    st = load_epic_state(cwd)
    if not st.get("active"):
        return {"ok": False, "status": st.get("status"), "reason": "not active"}

    text = read_active_context(cwd)
    fp = fingerprint_context(text)
    before = st.get("pending_fingerprint_before")
    handoff = extract_handoff_block(text)

    shape_errs = validate_active_context_shape(text)
    if shape_errs:
        reason = "activeContext shape FAIL: " + "; ".join(shape_errs)
        st["active"] = False
        st["status"] = "halted"
        st["halt_reason"] = reason
        save_epic_state(cwd, st)
        return {
            "ok": False,
            "status": "halted",
            "reason": reason,
            "fingerprint": fp,
            "shape_errors": shape_errs,
        }

    st["iteration"] = int(st.get("iteration") or 0) + 1
    hist = list(st.get("history") or [])
    hist.append(
        {
            "n": st["iteration"],
            "command": st.get("last_command"),
            "fingerprint": fp,
            "at": utc_now(),
        }
    )
    st["history"] = hist[-50:]

    if before is not None and fp == before:
        st["active"] = False
        st["status"] = "halted"
        st["halt_reason"] = "no Handoff/load_now progress after session"
        save_epic_state(cwd, st)
        return {
            "ok": False,
            "status": "halted",
            "reason": "no progress (same fingerprint)",
            "fingerprint": fp,
        }

    if HALT_RE.search(handoff):
        st["active"] = False
        st["status"] = "halted"
        st["halt_reason"] = "human gate after session"
        save_epic_state(cwd, st)
        return {
            "ok": False,
            "status": "halted",
            "reason": "human gate after session",
            "fingerprint": fp,
        }

    last_mode = command_mode(st.get("last_command") or "") if st.get("last_command") else None
    if last_mode == "IMPLEMENT":
        # Handoff Артефакт = факт сессии; pending мог ошибочно взять следующий sNN
        # из load_now с несколькими шагами — не halt по отсутствующему next-файлу.
        handoff_step = implement_step_from_handoff(handoff)
        pending_step = st.get("pending_implement_step")
        step_rel = handoff_step or pending_step
        if step_rel:
            errs = validate_implement_step_format(Path(cwd) / step_rel)
            if errs:
                reason = f"implement step format FAIL ({step_rel}): " + "; ".join(errs)
                st["active"] = False
                st["status"] = "halted"
                st["halt_reason"] = reason
                save_epic_state(cwd, st)
                return {
                    "ok": False,
                    "status": "halted",
                    "reason": reason,
                    "fingerprint": fp,
                    "pending_implement_step": step_rel,
                    "format_errors": errs,
                    "repairable": True,
                }
        else:
            reason = (
                "implement step format FAIL: не найден step path "
                "(Handoff Артефакт + pending_implement_step пусты)"
            )
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "repairable": True,
            }

    if re.search(r"(?i)—\s*blocked|\bblocked\b", handoff) and re.search(
        r"(?i)Handoff\s+.*\bQA\b", handoff
    ):
        # keep running only if next is BUGFIX — resolve_next will decide
        pass

    st["last_fingerprint"] = fp
    st["status"] = "running"
    st["active"] = True
    saved_pending_step = st.get("pending_implement_step")
    st["pending_implement_step"] = None
    save_epic_state(cwd, st)

    # complete only when next is ARCHIVE (ручной) or last session was REFLECT→ARCHIVE
    pending = decompose_pending_left(cwd, st.get("decompose"))
    load_now = assert_integ_yaml_shards(extract_load_now(text))
    last_mode = command_mode(st.get("last_command") or "") if st.get("last_command") else None

    # Advance canonical ledger via transitions.yaml — result.yaml REQUIRED
    try:
        import loop_engine as le
        from session_result import (
            clear_result,
            collect_test_commands_for_assert,
            load_and_normalize_result,
            pytest_assert_enabled,
            run_test_commands,
            validate_result,
        )

        result_data, norm_changes = load_and_normalize_result(
            cwd, track="epic", persist=True
        )
        if norm_changes:
            le.append_trace(
                cwd,
                {
                    "kind": "result_normalized",
                    "changes": norm_changes,
                    "result": result_data,
                },
                track="epic",
            )
        if not result_data:
            reason = "result.yaml missing (no handoff fallback)"
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            le.append_trace(cwd, {"kind": "halt", "reason": reason}, track="epic")
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "repairable": False,
            }
        if result_data.get("_invalid"):
            reason = f"result.yaml invalid: {result_data.get('_reason')}"
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            le.append_trace(
                cwd,
                {"kind": "halt", "reason": reason, "result": result_data},
                track="epic",
            )
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "repairable": True,
            }
        verrs = validate_result(result_data)
        if verrs:
            reason = "result.yaml validate FAIL: " + "; ".join(verrs)
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            le.append_trace(
                cwd,
                {"kind": "halt", "reason": reason, "result": result_data},
                track="epic",
            )
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "result": result_data,
                "repairable": True,
            }
        if result_data.get("status") == "halt":
            halt_epic(cwd, result_data.get("notes") or "result.yaml status=halt")
            return {
                "ok": False,
                "status": "halted",
                "reason": "result.yaml status=halt",
                "fingerprint": fp,
                "result": result_data,
            }

        step_for_check = (
            result_data.get("artifact")
            or implement_step_from_handoff(handoff)
            or saved_pending_step
        )
        # Machine pending queue: pop completed step_id from epic.remaining
        if (
            str(result_data.get("status") or "") == "ok"
            and (last_mode or "").upper() in {"IMPLEMENT", "REFACTOR"}
            and result_data.get("step_id")
        ):
            complete_epic_remaining_step(cwd, str(result_data.get("step_id")))
            pending = decompose_pending_left(cwd, st.get("decompose"))

        xerrs = crosscheck_ok_result(
            cwd,
            result_data,
            last_mode=last_mode,
            decompose=st.get("decompose"),
            step_path=step_for_check,
            handoff=handoff,
            verify_verdict=st.get("last_verify_verdict"),
        )
        if xerrs:
            reason = "result.yaml crosscheck FAIL: " + "; ".join(xerrs)
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            le.append_trace(
                cwd,
                {
                    "kind": "halt",
                    "reason": reason,
                    "result": result_data,
                    "verify_verdict": st.get("last_verify_verdict"),
                },
                track="epic",
            )
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "result": result_data,
                "crosscheck_errors": xerrs,
                "repairable": True,
            }

        if (
            pytest_assert_enabled()
            and str(result_data.get("status") or "") == "ok"
            and (last_mode or "").upper() in {"IMPLEMENT", "REFACTOR", "BUGFIX"}
            and not handoff_code_changed_no(handoff)
        ):
            test_cmds = collect_test_commands_for_assert(
                cwd,
                result_data,
                step_path=step_for_check,
            )
            if not test_cmds:
                reason = (
                    "result.yaml test assert FAIL: нет команд в "
                    "test_commands/pytest_commands / step tests: / ## Тесты "
                    "(status=ok + code_changed≠no)"
                )
                st["active"] = False
                st["status"] = "halted"
                st["halt_reason"] = reason
                save_epic_state(cwd, st)
                le.append_trace(
                    cwd,
                    {"kind": "halt", "reason": reason, "result": result_data},
                    track="epic",
                )
                return {
                    "ok": False,
                    "status": "halted",
                    "reason": reason,
                    "fingerprint": fp,
                    "result": result_data,
                }
            test_errs = run_test_commands(cwd, test_cmds)
            if test_errs:
                reason = "result.yaml test assert FAIL: " + " | ".join(test_errs)
                st["active"] = False
                st["status"] = "halted"
                st["halt_reason"] = reason
                save_epic_state(cwd, st)
                le.append_trace(
                    cwd,
                    {
                        "kind": "halt",
                        "reason": reason,
                        "test_commands": test_cmds,
                        "result": result_data,
                    },
                    track="epic",
                )
                return {
                    "ok": False,
                    "status": "halted",
                    "reason": reason,
                    "fingerprint": fp,
                    "result": result_data,
                    "test_commands": test_cmds,
                }
            le.append_trace(
                cwd,
                {
                    "kind": "test_assert",
                    "ok": True,
                    "test_commands": test_cmds,
                },
                track="epic",
            )

        adv = le.advance_ledger_after_session(
            cwd,
            last_mode=last_mode,
            handoff=handoff,
            role=st.get("role_prefix"),
            pending=pending,
            decompose=st.get("decompose"),
            load_now=load_now,
            model=st.get("model"),
            result=result_data,
            track="epic",
        )
        if not adv.get("ok"):
            reason = adv.get("reason") or "advance_ledger failed"
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "result": result_data,
                "event": adv.get("event"),
            }
        ledger_cmd = le.command_from_state(adv.get("state") or {})
        result_source = "result.yaml"
        clear_result(cwd, track="epic")
        if st.get("repair_attempt"):
            st["repair_attempt"] = 0
            save_epic_state(cwd, st)
    except Exception as exc:
        reason = f"after_session ledger error: {exc}"
        st["active"] = False
        st["status"] = "halted"
        st["halt_reason"] = reason
        save_epic_state(cwd, st)
        return {
            "ok": False,
            "status": "halted",
            "reason": reason,
            "fingerprint": fp,
        }

    nxt = ledger_cmd or ""
    mode = command_mode(nxt) if nxt else None

    if pending == 0 and mode == "ARCHIVE":
        complete_epic(cwd, "decompose done — ARCHIVE вручную")
        return {
            "ok": False,
            "status": "complete",
            "reason": "epic complete before ARCHIVE NOW (run manually)",
            "fingerprint": fp,
            "command": ledger_cmd,
            "result_source": result_source,
        }

    if pending == 0 and last_mode == "REFLECT" and mode in {None, "ARCHIVE"}:
        complete_epic(cwd, "REFLECT done — ARCHIVE вручную")
        return {
            "ok": False,
            "status": "complete",
            "reason": "epic complete after REFLECT (ARCHIVE вручную)",
            "fingerprint": fp,
            "result_source": result_source,
        }

    if pending == 0 and mode == "REFLECT":
        return {
            "ok": True,
            "status": "running",
            "reason": "REFLECT next (auto)",
            "fingerprint": fp,
            "pending_steps": pending,
            "ledger_command": ledger_cmd,
            "result_source": result_source,
        }

    return {
        "ok": True,
        "status": "running",
        "reason": "progress ok",
        "fingerprint": fp,
        "pending_steps": pending,
        "ledger_command": ledger_cmd,
        "result_source": result_source,
        "result": result_data,
    }


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
        "(новая сессия = чистый контекст)."
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
