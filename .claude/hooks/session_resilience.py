#!/usr/bin/env python3
"""Session resilience: abort detection, dirty resume, last-session marker."""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ABORT_PATTERNS = (
    re.compile(r"(?i)API Error:\s*terminated"),
    re.compile(r"(?i)API Error:\s*overloaded"),
    re.compile(r"(?i)API Error:\s*.*rate.?limit"),
    re.compile(r"(?i)stream ended unexpectedly"),
    re.compile(r"(?i)connection (?:reset|aborted|closed)"),
    re.compile(r"(?i)^KeyboardInterrupt"),
)

LAST_SESSION_NAME = "last-session.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def last_session_path(cwd: str | Path, *, track: str = "epic") -> Path:
    root = Path(cwd)
    return root / ".claude" / "runtime" / track / LAST_SESSION_NAME


def detect_abort_in_text(text: str) -> str | None:
    for pat in ABORT_PATTERNS:
        m = pat.search(text or "")
        if m:
            return m.group(0).strip()[:200]
    return None


def detect_abort_in_log(log_path: Path) -> str | None:
    if not log_path.is_file():
        return None
    try:
        # read tail — abort usually at end
        data = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if len(data) > 200_000:
        data = data[-200_000:]
    return detect_abort_in_text(data)


def git_dirty_paths(cwd: str | Path) -> list[str]:
    root = Path(cwd)
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain", "-uall"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        raise RuntimeError(f"git status failed: {exc}") from exc
    paths: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        # XY PATH or XY ORIG -> PATH
        rest = line[3:] if len(line) > 3 else line.strip()
        if " -> " in rest:
            rest = rest.split(" -> ", 1)[1]
        paths.append(rest.strip())
    return paths


def filter_step_dirty(
    dirty: list[str],
    *,
    step_id: str | None,
    delta_paths: list[str] | None = None,
) -> list[str]:
    """Keep dirty files related to current step / delta (not whole repo noise)."""
    sid = (step_id or "").lower()
    delta_norm = [p.replace("\\", "/") for p in (delta_paths or [])]
    kept: list[str] = []
    for p in dirty:
        norm = p.replace("\\", "/")
        if sid and sid in norm.lower():
            kept.append(norm)
            continue
        if any(
            x in norm
            for x in (
                "frontend/src/",
                "apps/api/",
                "apps/edge/",
                "tests/",
                "memory-bank/",
            )
        ):
            if delta_norm:
                if any(d in norm or norm in d for d in delta_norm if d):
                    kept.append(norm)
                    continue
                # code dirty while step in progress — still relevant
                if norm.startswith(("frontend/", "apps/", "tests/")):
                    kept.append(norm)
                    continue
            else:
                if norm.startswith(("frontend/", "apps/", "tests/")):
                    kept.append(norm)
    # unique preserve order
    seen: set[str] = set()
    out: list[str] = []
    for p in kept:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out[:40]


def write_last_session(
    cwd: str | Path,
    *,
    track: str,
    status: str,
    reason: str | None = None,
    step_id: str | None = None,
    implement: str | None = None,
    resume_from: str | None = None,
    dirty: list[str] | None = None,
    log_file: str | None = None,
    exit_code: int | None = None,
) -> Path:
    path = last_session_path(cwd, track=track)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": utc_now(),
        "status": status,
        "reason": reason,
        "step_id": step_id,
        "implement": implement,
        "resume_from": resume_from,
        "dirty": dirty or [],
        "log_file": log_file,
        "exit_code": exit_code,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_last_session(cwd: str | Path, *, track: str = "epic") -> dict[str, Any] | None:
    path = last_session_path(cwd, track=track)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def extract_paths_from_delta(delta: list[str]) -> list[str]:
    """Best-effort path extraction from delta bullet strings."""
    paths: list[str] = []
    pat = re.compile(
        r"(?:frontend/|apps/|tests/|memory-bank/)[^\s`'\"]+"
    )
    for item in delta:
        for m in pat.finditer(str(item)):
            paths.append(m.group(0).rstrip(".,);:"))
    return paths


def dirty_resume_prompt_lines(
    cwd: str | Path,
    *,
    step_id: str | None,
    delta: list[str] | None = None,
    resume_from: str | None = None,
    last: dict[str, Any] | None = None,
) -> list[str]:
    dirty = git_dirty_paths(cwd)
    related = filter_step_dirty(
        dirty,
        step_id=step_id,
        delta_paths=extract_paths_from_delta(delta or []),
    )
    aborted = bool(last and str(last.get("status") or "") == "aborted")
    if not related and not aborted:
        return []
    lines = ["", "## resume_dirty (HARD)"]
    if aborted:
        lines.append(
            f"prev_session: aborted"
            + (f" — {last.get('reason')}" if last and last.get("reason") else "")
        )
        if last and last.get("resume_from"):
            lines.append(f"prev_resume_from: {last['resume_from']}")
    if resume_from:
        lines.append(f"continue_from_checkpoint: {resume_from}")
    if related:
        lines.append("dirty_files (do NOT restart discovery; continue edits):")
        for p in related:
            lines.append(f"- {p}")
    lines.append(
        "FORBIDDEN: discard/revert dirty step files; re-do cp со status=done; "
        "full-repo rediscovery when dirty_files non-empty."
    )
    lines.append(
        "REQUIRED: Read dirty_files first → finish pending checkpoints → flush cp status."
    )
    return lines


def delta_paths_exist(cwd: str | Path, delta: list[str]) -> tuple[bool, list[str]]:
    """True if every extracted path from delta exists on disk (and ≥1 path found)."""
    root = Path(cwd)
    paths = extract_paths_from_delta(delta)
    if not paths:
        return False, []
    missing: list[str] = []
    for p in paths:
        if not (root / p).exists():
            missing.append(p)
    return (len(missing) == 0), missing
