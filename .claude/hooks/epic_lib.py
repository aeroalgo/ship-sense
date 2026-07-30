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
STATE_NAME = "state.json"
NEXT_PROMPT_NAME = "next-prompt.txt"

ALLOWED_DEFAULT = (
    "IMPLEMENT",
    "CREATIVE",
    "QA",
    "BUGFIX",
    "REFACTOR",
)

_MODE_ALT = (
    r"REFACTOR(?:\s+(?:PLAN|DECOMPOSE))?|"
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


def extract_load_now(text: str) -> list[str]:
    m = re.search(r"(?im)^##\s*load_now\s*$", text)
    if not m:
        return []
    rest = text[m.end() :]
    nxt = re.search(r"(?im)^##\s+", rest)
    body = rest[: nxt.start()] if nxt else rest
    paths: list[str] = []
    for line in body.splitlines():
        pm = re.search(
            r"`((?:memory-bank|apps|tests|migrations)/[^`]+)`",
            line,
        )
        if pm:
            paths.append(pm.group(1).strip())
    return paths


def fingerprint_context(text: str) -> str:
    handoff = extract_handoff_block(text)
    load = "\n".join(extract_load_now(text))
    raw = f"{handoff}\n---\n{load}".strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def parse_next_command(handoff: str) -> str | None:
    m = re.search(
        r"(?im)^\s*[-*]\s*\*\*Следующий:\*\*\s*(.+)$",
        handoff,
    )
    if not m:
        m = re.search(r"(?im)^\s*[-*]\s*\*\*Next:\*\*\s*(.+)$", handoff)
    if not m:
        return None
    line = m.group(1).strip()
    cm = CMD_RE.search(line)
    if cm:
        return re.sub(r"\s+", " ", cm.group(1)).upper().replace("ARCHIVE NOW", "ARCHIVE NOW")
    # link-only → IMPLEMENT of implied role from Handoff title
    title = re.search(r"(?im)^##\s*Handoff\s+(\w+)", handoff)
    role = (title.group(1).upper() if title else "BACK")
    if role not in {"BACK", "FRONT", "INTEG"}:
        role = "BACK"
    if re.search(r"(?i)\br\d{2}\b|refactor/", line):
        return f"{role} REFACTOR"
    if re.search(r"(?i)\bs\d{2}\b|\be\d{2}\b|implement/", line):
        return f"{role} IMPLEMENT"
    if re.search(r"(?i)creative/", line):
        return f"{role} CREATIVE"
    return None


def command_mode(cmd: str) -> str | None:
    m = ROLE_MODE_RE.match(cmd.strip())
    if not m:
        return None
    return m.group(2).upper().replace("ARCHIVE NOW", "ARCHIVE")


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


def decompose_pending_left(cwd: str | Path, decompose: str | None) -> int | None:
    idx = _decompose_index_path(cwd, decompose)
    if idx is None:
        return None
    text = idx.read_text(encoding="utf-8", errors="replace")
    pending = len(
        re.findall(
            r"(?im)\|\s*\*\*s\d{2}\*\*.*\|\s*(?:pending|active)\s*\|",
            text,
        )
    )
    pending += len(
        re.findall(
            r"(?im)\|\s*\*\*e\d{2}\*\*.*\|\s*(?:pending|active)\s*\|",
            text,
        )
    )
    pending += len(
        re.findall(
            r"(?im)\|\s*\*\*r\d{2}\*\*.*\|\s*(?:pending|active)\s*\|",
            text,
        )
    )
    # fallback: checklist unchecked
    if pending == 0:
        pending = len(re.findall(r"(?m)^-\s\[\s\]\s", text))
    return pending


def normalize_decompose_ref(cwd: str | Path, ref: str) -> str:
    ref = ref.strip().rstrip("/")
    root = Path(cwd)
    p = Path(ref)
    if p.is_file():
        return str(p.as_posix())
    if p.is_dir() and (p / "index.md").is_file():
        return str((p / "index.md").as_posix())
    # bare id — feature plan first, then refactor/plan
    for base in (
        root / "memory-bank" / "back" / "plan",
        root / "memory-bank" / "front" / "plan",
        root / "memory-bank" / "integration" / "plan",
        root / "memory-bank" / "back" / "refactor" / "plan",
        root / "memory-bank" / "front" / "refactor" / "plan",
        root / "memory-bank" / "integration" / "refactor" / "plan",
    ):
        for name in (ref, f"decompose-{ref}", ref.replace("decompose-", "")):
            cand = base / name
            if (cand / "index.md").is_file():
                return str((cand / "index.md").relative_to(root).as_posix())
            if cand.is_file():
                return str(cand.relative_to(root).as_posix())
    return ref


def arm_epic(
    cwd: str | Path,
    decompose: str,
    *,
    role_prefix: str = "BACK",
    max_iterations: int = 40,
    allowed_modes: list[str] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    st = default_state()
    st["active"] = True
    st["status"] = "running"
    st["decompose"] = normalize_decompose_ref(cwd, decompose)
    st["role_prefix"] = role_prefix.upper()
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
    return st


def halt_epic(cwd: str | Path, reason: str) -> dict[str, Any]:
    st = load_epic_state(cwd)
    st["active"] = False
    st["status"] = "halted"
    st["halt_reason"] = reason
    save_epic_state(cwd, st)
    return st


def complete_epic(cwd: str | Path, reason: str = "all steps done") -> dict[str, Any]:
    st = load_epic_state(cwd)
    st["active"] = False
    st["status"] = "complete"
    st["halt_reason"] = reason
    save_epic_state(cwd, st)
    return st


def _pick_allow_read_files(load_now: list[str], cmd: str) -> list[str]:
    """≤5 concrete files for reviewer/verify ALLOW READ (no dirs, no globs)."""
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
    return root_candidates[:5]


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
        if not rel_path.endswith(".md"):
            continue
        path = root / rel_path
        if not path.is_file():
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


def _mode_appendix(cmd: str, cwd: str | Path, load_now: list[str]) -> list[str]:
    mode = command_mode(cmd) or ""
    allow = _pick_allow_read_files(load_now, cmd)
    allow_line = ", ".join(allow) if allow else "memory-bank/activeContext.md, pyproject.toml"

    if mode == "QA":
        return [
            "",
            "## spawn-gate BACK QA (обязательно — без этого reviewer DENY)",
            "1. Parent прогоняет suite (не reviewer):",
            "   .venv/bin/pytest tests/storage/ -q",
            "   .venv/bin/pytest -m 'not slow' -q",
            "2. Один раз Agent subagent_type=reviewer. Prompt — секции с новой строки, без markdown-заголовков ##:",
            "Suite results:",
            "- (числа passed/failed из твоих pytest)",
            "AC+:",
            "- storage scope green / contracts",
            "AC−:",
            "- не full suite green если slow не завершён",
            "- не mocks = live compose",
            "§0.11:",
            "- DATABASE_URL / SHIPSSENSE_WRITER_ENDPOINT ↔ docker-compose.yml",
            f"ALLOW READ: {allow_line}",
            "FORBID: edit; pytest; explore; .cursor/rules/**; деревья в ALLOW",
            "Отчёт: VERDICT PASS|BLOCKED|FAIL",
            "3. FINISH: qa-*.md + перезаписать ЕДИНСТВЕННЫЙ ## Handoff BACK QA в activeContext "
            "(replace, не append; pass→next; blocked→BUGFIX)",
            "ЗАПРЕЩЕНО: ALLOW READ с ** или каталогами; >5 файлов; spawn reviewer без Suite results.",
        ]

    explorer_gate = [
        "",
        "## spawn-gate SEARCH (обязательно — без этого широкий rg DENY)",
        "Если нужен codebase search / import audit / where-is / multi-file map:",
        "сначала один раз Agent subagent_type=explorer (не built-in Explore). Prompt — секции с новой строки:",
        "Цель:",
        "- (что найти: imports / owners / paths по текущему step)",
        "GRAPHIFY:",
        "- query \"<символы/пакеты текущего step>\"",
        f"ALLOW READ: {allow_line}",
        "FORBID: edit; role-command; plan; деревья в ALLOW; >5 файлов",
        "Отчёт: file:line. На русском.",
        "FORBIDDEN parent: серия rg/grep -R по apps|tests|frontend вместо explorer.",
        "Исключение: правки только по явному file list shard без discovery.",
    ]

    if mode == "IMPLEMENT":
        verify_cmds = _extract_verify_commands(cwd, load_now)
        verify_lines = verify_cmds or [".venv/bin/pytest <targeted-test-from-step-shard> -q"]
        return [
            *explorer_gate,
            "",
            "## spawn-gate IMPLEMENT (обязательно — без этого verify DENY)",
            "Если code_changed=yes: один раз Agent subagent_type=verify. Prompt — секции с новой строки, без markdown-заголовков ##:",
            "AC+:",
            "- targeted pytest green по текущему step",
            "- AC шага подтверждён кодом/тестом",
            "AC−:",
            "- не ломать compose/runtime entrypoint и текущий публичный API",
            "- не выходить за scope текущего step / diff",
            "§0.11:",
            "- каждая внешняя ссылка/ENV/API/entrypoint из diff имеет counterpart в code/tests/compose",
            "VERIFY:",
            *[f"- {line}" for line in verify_lines],
            f"ALLOW READ: {allow_line}",
            "FORBID: edit; .cursor/rules/**; деревья в ALLOW; >5 файлов; пустой AC−/§0.11.",
            "Отчёт: VERDICT PASS|FAIL",
        ]

    if mode == "REFACTOR":
        verify_cmds = _extract_verify_commands(cwd, load_now)
        verify_lines = verify_cmds or [".venv/bin/pytest <targeted-test-from-rNN-shard> -q"]
        return [
            *explorer_gate,
            "",
            "## spawn-gate REFACTOR (обязательно — без этого verify DENY)",
            "Behavior freeze: не менять внешний контракт/API/UX без явного scope.",
            "green before → refactor → green after. Один rNN за сессию.",
            "Если code_changed=yes: один раз Agent subagent_type=verify. Prompt — секции с новой строки, без markdown-заголовков ##:",
            "AC+:",
            "- targeted pytest green до и после refactor (rNN scope)",
            "- поведение/контракт сохранены (behavior freeze)",
            "AC−:",
            "- не менять публичный API/контракт вне явного scope rNN",
            "- не выходить за scope текущего rNN / diff",
            "§0.11:",
            "- каждый env/event/api/storage counterpart из diff подтверждён в code/tests/config",
            "VERIFY:",
            *[f"- {line}" for line in verify_lines],
            f"ALLOW READ: {allow_line}",
            "FORBID: edit; .cursor/rules/**; деревья в ALLOW; >5 файлов; пустой AC−/§0.11.",
            "Отчёт: VERDICT PASS|FAIL",
        ]

    if mode == "BUGFIX":
        verify_cmds = _extract_verify_commands(cwd, load_now)
        verify_lines = verify_cmds or [".venv/bin/pytest <targeted-test-from-bugfix-shard> -q"]
        return [
            *explorer_gate,
            "",
            "## spawn-gate BUGFIX (если code_changed=yes — без packed verify не FINISH)",
            "Root-cause fix → targeted pytest → при code_changed один раз Agent subagent_type=verify.",
            "AC+:",
            "- targeted pytest green по bugfix scope",
            "- root cause закрыт минимальным fix без fallback/hide-error",
            "AC−:",
            "- не ломать соседний runtime/API вне bugfix scope",
            "- не расширять diff сверх root-cause fix",
            "§0.11:",
            "- каждый env/event/api/storage counterpart из diff подтверждён в code/tests/config",
            "VERIFY:",
            *[f"- {line}" for line in verify_lines],
            f"ALLOW READ: {allow_line}",
            "FORBID: edit внутри verify; .cursor/rules/**; деревья в ALLOW; >5 файлов.",
            "Отчёт verify: VERDICT PASS|FAIL",
        ]

    if mode == "CREATIVE":
        return [
            "",
            "## CREATIVE batch",
            "Один creative-файл → rewire needs_creative closed → Handoff Next: BACK IMPLEMENT.",
        ]

    return []


def build_prompt(cmd: str, cwd: str | Path, load_now: list[str]) -> str:
    lines = [
        cmd,
        "",
        "EPIC MODE (автоцикл): ровно один atomic шаг в этой сессии.",
        "После FINISH: в activeContext.md оставь РОВНО ОДИН ## Handoff (полная перезапись/replace, не append стопки) + обнови load_now; остановь turn (stop-hook).",
        "FORBIDDEN: два и более ## Handoff в activeContext — история только в tasks/log и step/qa shards.",
        "Не начинай следующий sNN/rNN/CREATIVE/QA в этой же сессии — epic-loop поднимет новую claude -p.",
        "Не /exit и не /clear — loop сам перезапускает сессию с чистым контекстом.",
        "Старт:",
        "1. memory-bank/activeContext.md → load_now + единственный §Handoff",
    ]
    if load_now:
        lines.append(f"2. {load_now[0]}")
        for i, p in enumerate(load_now[1:3], start=3):
            lines.append(f"{i}. {p}")
    else:
        lines.append("2. shard из Handoff / decompose index (первый pending/active)")
    lines.append("")
    lines.append("New chat / clear — делает epic-loop (headless -p); сам /clear и /exit не вызывай.")
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
    load_now = extract_load_now(text)

    if HALT_RE.search(handoff) or HALT_RE.search(text[:2000]):
        halt_epic(cwd, "human gate in Handoff/context")
        return {
            "ok": False,
            "status": "halted",
            "command": None,
            "prompt": None,
            "reason": "human/grill-me gate",
        }

    # QA blocked → only BUGFIX/QA allowed
    if re.search(r"(?i)Handoff\s+.*\bQA\b", handoff) and re.search(
        r"(?i)—\s*blocked|\bblocked\b", handoff
    ):
        cmd_guess = parse_next_command(handoff) or ""
        mode = command_mode(cmd_guess) if cmd_guess else None
        if mode not in {"BUGFIX", "QA"}:
            halt_epic(cwd, "QA blocked — next must be BUGFIX or QA")
            return {
                "ok": False,
                "status": "halted",
                "command": cmd_guess or None,
                "prompt": None,
                "reason": "QA blocked without BUGFIX/QA next",
            }

    cmd = parse_next_command(handoff)
    if not cmd:
        # bootstrap from decompose if no handoff next
        pending = decompose_pending_left(cwd, st.get("decompose"))
        if pending == 0:
            complete_epic(cwd, "decompose has no pending steps")
            return {
                "ok": False,
                "status": "complete",
                "command": None,
                "prompt": None,
                "reason": "epic complete (no pending)",
            }
        role = st.get("role_prefix") or "BACK"
        if is_refactor_decompose(cwd, st.get("decompose")):
            cmd = f"{role} REFACTOR"
        else:
            cmd = f"{role} IMPLEMENT"

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
    if mode == "ARCHIVE":
        mode_key = "ARCHIVE"
    else:
        mode_key = mode

    outside_auto = {
        "REFLECT",
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
        if mode_key == "REFLECT":
            # last optional reflect then complete after this run
            pass
        else:
            complete_epic(cwd, f"next phase outside epic auto: {cmd}")
            return {
                "ok": False,
                "status": "complete",
                "command": cmd,
                "prompt": None,
                "reason": f"epic complete before {cmd}",
            }

    if mode_key not in allowed and mode_key != "REFLECT":
        halt_epic(cwd, f"mode {mode_key} not in allowed_modes")
        return {
            "ok": False,
            "status": "halted",
            "command": cmd,
            "prompt": None,
            "reason": f"mode not allowed: {mode_key}",
        }

    pending = decompose_pending_left(cwd, st.get("decompose"))
    if pending == 0 and mode_key in {"IMPLEMENT", "REFACTOR"}:
        # allow QA after last implement/refactor step
        if "QA" in allowed:
            cmd = f"{st.get('role_prefix') or 'BACK'} QA"
            mode_key = "QA"
        else:
            complete_epic(cwd, "no pending implement/refactor steps")
            return {
                "ok": False,
                "status": "complete",
                "command": None,
                "prompt": None,
                "reason": "epic complete",
            }

    prompt = build_prompt(cmd, cwd, load_now)
    next_prompt_path(cwd).write_text(prompt + "\n", encoding="utf-8")

    st["last_command"] = cmd
    st["pending_fingerprint_before"] = fp
    save_epic_state(cwd, st)

    return {
        "ok": True,
        "status": "running",
        "command": cmd,
        "prompt": prompt,
        "reason": None,
        "fingerprint": fp,
        "load_now": load_now,
        "pending_steps": pending,
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
        halt_epic(cwd, "no Handoff/load_now progress after session")
        st = load_epic_state(cwd)
        return {
            "ok": False,
            "status": "halted",
            "reason": "no progress (same fingerprint)",
            "fingerprint": fp,
        }

    if HALT_RE.search(handoff):
        halt_epic(cwd, "human gate after session")
        return {
            "ok": False,
            "status": "halted",
            "reason": "human gate after session",
            "fingerprint": fp,
        }

    if re.search(r"(?i)—\s*blocked|\bblocked\b", handoff) and re.search(
        r"(?i)Handoff\s+.*\bQA\b", handoff
    ):
        # keep running only if next is BUGFIX — resolve_next will decide
        pass

    st["last_fingerprint"] = fp
    st["status"] = "running"
    st["active"] = True
    save_epic_state(cwd, st)

    # complete if decompose empty and next is reflect/archive/done wording
    pending = decompose_pending_left(cwd, st.get("decompose"))
    nxt = parse_next_command(handoff) or ""
    mode = command_mode(nxt) if nxt else None
    if pending == 0 and mode in {None, "REFLECT", "ARCHIVE"}:
        if mode == "REFLECT":
            return {
                "ok": True,
                "status": "running",
                "reason": "optional REFLECT next",
                "fingerprint": fp,
            }
        complete_epic(cwd, "decompose done")
        return {
            "ok": False,
            "status": "complete",
            "reason": "epic complete",
            "fingerprint": fp,
        }

    return {
        "ok": True,
        "status": "running",
        "reason": "progress ok",
        "fingerprint": fp,
        "pending_steps": pending,
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
        "Не вызывай /clear и не стартуй следующий шаг — это делает scripts/epic-loop.sh "
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
