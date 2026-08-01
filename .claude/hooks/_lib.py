#!/usr/bin/env python3
"""Shared spawn-gate state for Claude Code hooks (ship-sense)."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Custom overlay only — gates + cheap search. Built-in Agent types untouched.
CUSTOM_OVERLAY = frozenset({"verify", "reviewer", "explorer"})
GATE_AGENTS = frozenset({"verify", "reviewer"})
ALLOWED = CUSTOM_OVERLAY

ALIAS: dict[str, str] = {}

HARD_RULE = (
    "HARD RULE: ты subagent. НЕ запускай frontend-тесты "
    "(vitest/playwright/npm test/e2e). Отчёт parent — на русском."
)

PINNED_MODEL_AGENTS = CUSTOM_OVERLAY
NO_WORKTREE_AGENTS = CUSTOM_OVERLAY

CONTRACTS = {
    "verify": (
        "CONTRACT verify: нужен AC+ · AC− · §0.11 · VERIFY · RESULT · ALLOW. "
        "Итог строго VERDICT: PASS|FAIL. Не edit. Без isolation=worktree."
    ),
    "reviewer": (
        "CONTRACT reviewer: нужен Suite results · AC+ · AC− · §0.11 · ALLOW. "
        "Итог VERDICT: PASS|BLOCKED|FAIL. Не pytest. Не Plan Mode / plan-файлы. "
        "Без isolation=worktree."
    ),
    "explorer": (
        "CONTRACT explorer: поиск only (graphify). Желательно GRAPHIFY + ALLOW. "
        "Не edit. Не Plan Mode / plan-файлы — только конкретный отчёт на русском. "
        "Без isolation=worktree."
    ),
}

_SECTION_PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    "reviewer": [
        ("Suite results", re.compile(r"(?im)^\s*Suite results\b")),
        ("AC+", re.compile(r"(?im)^\s*AC\+\s*[:：]?")),
        ("AC−", re.compile(r"(?im)^\s*AC[−\-]\s*[:：]?")),
        ("§0.11", re.compile(r"(?im)^\s*§?\s*0\.11\s*[:：]?")),
        ("ALLOW READ", re.compile(r"(?im)^\s*ALLOW READ\s*[:：]?")),
    ],
    "verify": [
        ("AC+", re.compile(r"(?im)^\s*AC\+\s*[:：]?")),
        ("AC−", re.compile(r"(?im)^\s*AC[−\-]\s*[:：]?")),
        ("§0.11", re.compile(r"(?im)^\s*§?\s*0\.11\s*[:：]?")),
        ("VERIFY", re.compile(r"(?im)^\s*VERIFY\s*[:：]?")),
        ("RESULT", re.compile(r"(?im)^\s*RESULT\s*[:：]?")),
        ("ALLOW READ", re.compile(r"(?im)^\s*ALLOW READ\s*[:：]?")),
    ],
}

_NEXT_SECTION = re.compile(
    r"(?im)^\s*(?:Suite results|AC\+|AC[−\-]|§?\s*0\.11|VERIFY|RESULT|ALLOW READ|"
    r"FORBID|CREATE/EDIT|GRAPHIFY|Цель|Цель:|Budget|Отчёт|HARD RULE|"
    r"CONTRACT|Scope:)\b"
)

_ALLOW_PATH = re.compile(
    r"(?:^|[\s,`])("
    r"(?:apps|tests|memory-bank|migrations|frontend|\.claude|\.cursor|\.kilo)/"
    r"[^\s,`]+"
    r"|(?:pyproject\.toml|docker-compose\.ya?ml|alembic\.ini|"
    r"pytest\.ini|setup\.cfg|CLAUDE\.md|README\.md)"
    r")"
)

SPAWN_MAP = """## spawn-gate (Claude Code)
Делегирование — как обычно у Claude Code (Agent / built-in). Не запрещай spawn.
Overlay: @explorer (поиск, haiku) · @verify (pre-FINISH) · @reviewer (QA).
| Ситуация | Agent |
| Поиск «где X» | @explorer (опц.) или built-in Explore |
| Pre-FINISH code_changed | `@verify` ОБЯЗАТЕЛЬНО (step on disk → AC+/AC−/§0.11/VERIFY/RESULT/ALLOW ≤10); FAIL/DENY→fix→retry до PASS |
| BACK QA после suite | @reviewer ОБЯЗАТЕЛЬНО (Suite+AC+§0.11/ALLOW ≤10) |
FAIL: @verify после VERDICT: PASS. FAIL verify/reviewer: isolation=worktree; model=; ALLOW=дерево; нет секций.
QA FINISH: Handoff в activeContext обязателен.
Канон: `.claude/instructions/spawn-hard.md`
"""


def read_stdin() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


def emit(obj: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))


def state_path(session_id: str, cwd: str) -> Path:
    root = Path(cwd or os.getcwd())
    d = root / ".claude" / "runtime" / "spawn-gate"
    d.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", session_id or "nosession")[:80]
    return d / f"{safe}.json"


def load_state(session_id: str, cwd: str) -> dict[str, Any]:
    p = state_path(session_id, cwd)
    default = {
        "mode": None,
        "need_verify": False,
        "need_reviewer": False,
        "verify_done": False,
        "reviewer_done": False,
        "verify_verdict": None,
        "reviewer_verdict": None,
        "spawns": [],
    }
    if not p.is_file():
        return dict(default)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        for k, v in default.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return dict(default)


def save_state(session_id: str, cwd: str, state: dict[str, Any]) -> None:
    p = state_path(session_id, cwd)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_type(name: str | None) -> str | None:
    if not name:
        return None
    if name in ALIAS:
        return ALIAS[name]
    return name


def extract_verdict(text: str | None) -> str | None:
    if not text:
        return None
    m = re.search(r"VERDICT:\s*(PASS|FAIL|BLOCKED)\b", text, re.I)
    return m.group(1).upper() if m else None


def missing_contract_sections(agent: str | None, prompt: str) -> list[str]:
    if not agent or agent not in _SECTION_PATTERNS:
        return []
    missing: list[str] = []
    for label, pat in _SECTION_PATTERNS[agent]:
        if not pat.search(prompt or ""):
            missing.append(label)
    return missing


def _allow_section_body(prompt: str) -> str | None:
    m = re.search(r"(?im)^\s*ALLOW READ\s*[:：]?\s*(.*)$", prompt or "")
    if not m:
        m = re.search(r"(?im)^\s*ALLOW\s*[:：]\s*(.*)$", prompt or "")
    if not m:
        return None
    start = m.end()
    first = (m.group(1) or "").strip()
    lines = [first] if first else []
    for line in (prompt or "")[start:].splitlines():
        if _NEXT_SECTION.match(line) and not re.match(
            r"(?im)^\s*ALLOW READ\b", line
        ):
            break
        lines.append(line)
    return "\n".join(lines)


ALLOW_READ_MAX = 10


def allow_read_violations(prompt: str) -> list[str]:
    """Return human-readable violations for ALLOW READ (≤ALLOW_READ_MAX files, no dirs)."""
    body = _allow_section_body(prompt)
    if body is None:
        return []

    paths: list[str] = []
    seen: set[str] = set()
    for m in _ALLOW_PATH.finditer(body):
        t = m.group(1).strip().strip("`").rstrip(",;")
        if not t or t in seen:
            continue
        seen.add(t)
        paths.append(t)

    viol: list[str] = []
    trees: list[str] = []
    files: list[str] = []
    for p in paths:
        name = Path(p.rstrip("/")).name
        is_file = (
            not p.endswith("/")
            and (
                "." in name
                or name in {"Dockerfile", "Makefile", "LICENSE"}
            )
        )
        if p.endswith("/") or not is_file:
            trees.append(p)
        else:
            files.append(p)

    if trees:
        viol.append(
            f"ALLOW READ содержит деревья/каталоги (нужны ≤{ALLOW_READ_MAX} файлов): "
            + ", ".join(trees[:8])
        )
    if len(files) > ALLOW_READ_MAX:
        viol.append(
            f"ALLOW READ: {len(files)} файлов > {ALLOW_READ_MAX} — урежь список"
        )
    if not files and not trees:
        viol.append(
            f"ALLOW READ пуст — укажи ≤{ALLOW_READ_MAX} конкретных файлов"
        )
    return viol


def normalize_agent_tool_input(tool_input: dict[str, Any], norm: str | None) -> list[str]:
    """Mutate tool_input: strip worktree isolation + model override. Return notes."""
    notes: list[str] = []
    if not norm or norm not in ALLOWED:
        return notes

    iso = tool_input.get("isolation")
    if norm in NO_WORKTREE_AGENTS and iso and str(iso).lower() == "worktree":
        tool_input.pop("isolation", None)
        notes.append("stripped isolation=worktree (shared parent cwd; uncommitted diff)")

    if norm in PINNED_MODEL_AGENTS and "model" in tool_input:
        tool_input.pop("model", None)
        notes.append("stripped model= (use pin from .claude/agents/<type>.md)")

    return notes


FINISH_RE = re.compile(
    r"(?i)\b(FINISH|Handoff|step-файл|qa-\d{8}|activeContext|doc-router)\b"
)
IMPL_RE = re.compile(r"(?i)\bBACK\s+IMPLEMENT\b|\bIMPLEMENT\b.*\bs\d{2}\b")
QA_RE = re.compile(r"(?i)\bBACK\s+QA\b")
