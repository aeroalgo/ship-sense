#!/usr/bin/env python3
"""Machine session result — канон исхода сессии для loop runner.

Порядок (HARD):
  resolve → stub result.yaml (status=pending, draft=true)
  agent финализирует status → ok|blocked|fail|halt|gaps
  @verify только читает finalized result
  after → normalize aliases → validate + crosscheck + optional pytest assert → apply_event

Normalize (auto): status pass|passed|success → ok; QA status↔verdict.
Repairable validate/crosscheck FAIL → loop.sh до 3× prepare-repair session.
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

import yaml

RESULT_NAME = "result.yaml"
VALID_STATUS = frozenset({"ok", "blocked", "fail", "halt", "gaps"})
STUB_STATUS = "pending"
VALID_VERDICT = frozenset({"pass", "blocked", "fail"})
# Agents often put QA verdict into status; coerce before validate/halt.
STATUS_ALIASES = {
    "pass": "ok",
    "passed": "ok",
    "success": "ok",
    "successful": "ok",
    "done": "ok",
    "complete": "ok",
    "completed": "ok",
}
_QA_VERDICT_TO_STATUS = {"pass": "ok", "blocked": "blocked", "fail": "fail"}
_PYTEST_PREFIX = ".venv/bin/pytest "
_ALLOWED_TEST_PREFIXES = (
    _PYTEST_PREFIX,
    "cd frontend && npm exec vitest",
    "cd frontend && npm exec tsc",
    "npm exec vitest",
    "npm exec tsc",
)


def result_path(cwd: str | Path, track: str = "epic") -> Path:
    # Outside .claude/ — Claude Code treats .claude/** as protected path
    # (dontAsk auto-denies Write/Edit there). loop/ is writable in headless epic.
    return Path(cwd) / "loop" / "runtime" / track / RESULT_NAME


def default_result(
    *,
    status: str = "ok",
    verdict: str | None = None,
    step_id: str | None = None,
    artifact: str | None = None,
    role: str | None = None,
    mode: str | None = None,
    target: str | None = None,
    notes: str | None = None,
    gap: str | None = None,
    resume_command: str | None = None,
    resume_implement: str | None = None,
    draft: bool | None = None,
    pytest_commands: list[str] | None = None,
    test_commands: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "version": 1,
        "status": status,
        "verdict": verdict,
        "step_id": step_id,
        "artifact": artifact,
        "role": role,
        "mode": mode,
        "target": target,
        "gap": gap,
        "resume_command": resume_command,
        "resume_implement": resume_implement,
        "draft": draft,
        "pytest_commands": pytest_commands,
        "test_commands": test_commands,
        "notes": notes,
    }


def is_finalized_result(data: dict[str, Any] | None) -> bool:
    if not data or not isinstance(data, dict) or data.get("_invalid"):
        return False
    if data.get("draft") is True:
        return False
    return data.get("status") in VALID_STATUS


def normalize_result(
    data: dict[str, Any] | None,
    *,
    cwd: str | Path | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Coerce common agent mistakes in result.yaml. Does not touch pending stubs.

    Returns (normalized_copy_or_None, list of change descriptions).
    """
    if not data or not isinstance(data, dict) or data.get("_invalid"):
        return data, []
    if data.get("draft") is True or data.get("status") == STUB_STATUS:
        return dict(data), []

    out = dict(data)
    changes: list[str] = []
    raw_status = out.get("status")
    status_s = str(raw_status).strip().lower() if raw_status is not None else ""
    mode = str(out.get("mode") or "").upper()
    verdict = out.get("verdict")
    verdict_s = str(verdict).strip().lower() if verdict is not None else None

    if status_s in STATUS_ALIASES and status_s not in VALID_STATUS:
        new_status = STATUS_ALIASES[status_s]
        changes.append(f"status {raw_status!r}→{new_status!r}")
        out["status"] = new_status
        status_s = new_status
        # If agent used verdict word as status and left verdict empty — fill for QA.
        if mode == "QA" and verdict_s is None and status_s == "ok" and raw_status is not None:
            alias_as_verdict = str(raw_status).strip().lower()
            if alias_as_verdict in {"pass", "passed"}:
                out["verdict"] = "pass"
                verdict_s = "pass"
                changes.append("verdict null→pass (from status alias)")

    if mode == "QA":
        if verdict_s in _QA_VERDICT_TO_STATUS:
            expected = _QA_VERDICT_TO_STATUS[verdict_s]
            cur = str(out.get("status") or "")
            if cur != expected:
                changes.append(f"QA status {cur!r}→{expected!r} (verdict={verdict_s})")
                out["status"] = expected
        elif out.get("status") in VALID_STATUS and verdict_s is None:
            # status alone for QA — infer verdict when unambiguous
            cur = str(out.get("status"))
            inferred = {"ok": "pass", "blocked": "blocked", "fail": "fail"}.get(cur)
            if inferred:
                out["verdict"] = inferred
                changes.append(f"QA verdict null→{inferred} (from status)")

    if cwd and out.get("artifact"):
        try:
            import epic_yaml as ey

            coerced, msg = ey.coerce_epic_artifact_path(cwd, str(out["artifact"]))
            if msg and coerced:
                out["artifact"] = coerced
                changes.append(msg)
        except Exception:
            pass

    return out, changes


def validate_result(data: dict[str, Any] | None) -> list[str]:
    if not data or not isinstance(data, dict):
        return ["result missing or not a mapping"]
    errs: list[str] = []
    if data.get("draft") is True:
        errs.append("result still draft=true — finalize before after/verify")
    status = data.get("status")
    if status == STUB_STATUS:
        errs.append(
            f"status={STUB_STATUS!r} is stub only — set ok|blocked|fail|halt|gaps before verify/after"
        )
    elif status not in VALID_STATUS:
        errs.append(f"status must be one of {sorted(VALID_STATUS)}, got {status!r}")
    verdict = data.get("verdict")
    if verdict is not None and verdict not in VALID_VERDICT:
        errs.append(f"verdict must be one of {sorted(VALID_VERDICT)} or null, got {verdict!r}")
    mode = str(data.get("mode") or "").upper()
    if mode == "QA":
        if verdict not in VALID_VERDICT:
            errs.append("QA result requires verdict: pass|blocked|fail")
        elif status in VALID_STATUS:
            expected = {"pass": "ok", "blocked": "blocked", "fail": "fail"}[str(verdict)]
            if status != expected:
                errs.append(
                    f"QA status={status!r} incompatible with verdict={verdict!r} "
                    f"(expected {expected})"
                )
    if status == "ok" and verdict == "fail":
        errs.append("status=ok incompatible with verdict=fail")
    if status == "ok" and verdict == "blocked":
        errs.append("status=ok incompatible with verdict=blocked")
    cmds = data.get("pytest_commands")
    if cmds is not None:
        if not isinstance(cmds, list):
            errs.append("pytest_commands must be a list of strings")
        else:
            for c in cmds:
                if not isinstance(c, str) or not c.strip().startswith(_PYTEST_PREFIX):
                    errs.append(f"pytest_commands entry must start with {_PYTEST_PREFIX!r}: {c!r}")
    test_cmds = data.get("test_commands")
    if test_cmds is not None:
        if not isinstance(test_cmds, list):
            errs.append("test_commands must be a list of strings")
        else:
            for c in test_cmds:
                if not isinstance(c, str) or not is_allowed_test_command(c):
                    errs.append(
                        f"test_commands entry must be allowed pytest/vitest/tsc: {c!r}"
                    )
    return errs


def load_result(cwd: str | Path, track: str = "epic") -> dict[str, Any] | None:
    path = result_path(cwd, track)
    if not path.is_file():
        return None
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return None
    if not isinstance(raw, dict):
        return {"_invalid": True, "_reason": "result.yaml root must be a mapping"}
    return raw


def save_result(
    cwd: str | Path,
    data: dict[str, Any],
    *,
    track: str = "epic",
) -> Path:
    path = result_path(cwd, track)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = dict(default_result())
    body.update(data)
    body["version"] = int(body.get("version") or 1)
    # drop null-only noise keys for stub readability
    dump = {k: v for k, v in body.items() if v is not None}
    path.write_text(
        yaml.safe_dump(dump, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return path


def load_and_normalize_result(
    cwd: str | Path,
    track: str = "epic",
    *,
    persist: bool = True,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Load result.yaml, normalize aliases, optionally rewrite file."""
    data = load_result(cwd, track=track)
    normalized, changes = normalize_result(data, cwd=cwd)
    if persist and normalized is not None and changes and not normalized.get("_invalid"):
        save_result(cwd, normalized, track=track)
    return normalized, changes


def write_stub_result(
    cwd: str | Path,
    *,
    track: str = "epic",
    role: str | None = None,
    mode: str | None = None,
    step_id: str | None = None,
    artifact: str | None = None,
) -> Path:
    """Create pending draft for the session. Agent must finalize before @verify."""
    return save_result(
        cwd,
        {
            "status": STUB_STATUS,
            "draft": True,
            "role": role,
            "mode": mode,
            "step_id": step_id,
            "artifact": artifact,
            "notes": "stub — finalize status before @verify",
        },
        track=track,
    )


def clear_result(cwd: str | Path, track: str = "epic") -> bool:
    path = result_path(cwd, track)
    if path.is_file():
        path.unlink()
        return True
    return False


def event_from_result(data: dict[str, Any]) -> str:
    """Map machine result.yaml → transitions.yaml event. Raises ValueError if invalid."""
    errs = validate_result(data)
    if errs:
        raise ValueError("; ".join(errs))
    status = str(data["status"])
    verdict = data.get("verdict")
    if status == "halt":
        return "human_halt"
    if status == "gaps":
        return "gaps_found"
    if status == "blocked" or verdict == "blocked":
        return "finish_blocked"
    if status == "fail" or verdict == "fail":
        return "finish_fail"
    return "finish_ok"


def is_allowed_test_command(cmd: str) -> bool:
    cmd = normalize_test_command_entry(cmd)
    return any(cmd.startswith(prefix) for prefix in _ALLOWED_TEST_PREFIXES)


def normalize_test_command_entry(entry: str) -> str:
    cmd = entry.strip()
    if cmd.startswith("- "):
        cmd = cmd[2:].strip()
    if cmd.startswith("`") and cmd.endswith("`"):
        cmd = cmd[1:-1].strip()
    else:
        m = re.search(r"`([^`]+)`", cmd)
        if m:
            cmd = m.group(1).strip()
    return cmd


def _add_test_cmd(cmd: str, seen: set[str], out: list[str]) -> None:
    cmd = normalize_test_command_entry(cmd)
    if not is_allowed_test_command(cmd) or cmd in seen:
        return
    seen.add(cmd)
    out.append(cmd)


def _add_pytest_cmd(cmd: str, seen: set[str], out: list[str]) -> None:
    cmd = normalize_test_command_entry(cmd)
    if not cmd.startswith(_PYTEST_PREFIX) or cmd in seen:
        return
    seen.add(cmd)
    out.append(cmd)


def extract_pytest_commands_from_text(text: str, *, section: str | None = "## Тесты") -> list[str]:
    """Parse `.venv/bin/pytest …` from markdown (optionally only under a section)."""
    body = text
    if section:
        m = re.search(
            rf"(?ims)^{re.escape(section)}\s*\n(.*?)(?=^##\s|\Z)",
            text,
        )
        if m:
            body = m.group(1)
    commands: list[str] = []
    seen: set[str] = set()
    for raw in body.splitlines():
        if _PYTEST_PREFIX not in raw:
            continue
        line = raw.strip()
        if "`" in line:
            for part in re.findall(r"`([^`]+)`", line):
                _add_pytest_cmd(part, seen, commands)
        else:
            _add_pytest_cmd(line, seen, commands)
    return commands[:5]


def extract_pytest_commands_from_file(path: Path, *, section: str | None = "## Тесты") -> list[str]:
    if not path.is_file():
        return []
    try:
        return extract_pytest_commands_from_text(
            path.read_text(encoding="utf-8"),
            section=section,
        )
    except OSError:
        return []


def extract_test_commands_from_yaml_tests(tests: list[str]) -> list[str]:
    commands: list[str] = []
    seen: set[str] = set()
    for raw in tests:
        if isinstance(raw, str):
            _add_test_cmd(raw, seen, commands)
    return commands[:5]


def extract_test_commands_from_yaml_file(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return []
    if not isinstance(data, dict):
        return []
    tests = data.get("tests")
    if isinstance(tests, list):
        return extract_test_commands_from_yaml_tests(tests)
    return []


def extract_test_commands_from_text(text: str, *, section: str | None = "## Тесты") -> list[str]:
    body = text
    if section:
        m = re.search(
            rf"(?ims)^{re.escape(section)}\s*\n(.*?)(?=^##\s|\Z)",
            text,
        )
        if m:
            body = m.group(1)
    commands: list[str] = []
    seen: set[str] = set()
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if is_allowed_test_command(line) or "`" in line or _PYTEST_PREFIX in line:
            if "`" in line:
                for part in re.findall(r"`([^`]+)`", line):
                    _add_test_cmd(part, seen, commands)
            _add_test_cmd(line, seen, commands)
    return commands[:5]


def extract_test_commands_from_file(path: Path, *, section: str | None = "## Тесты") -> list[str]:
    if not path.is_file():
        return []
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return extract_test_commands_from_yaml_file(path)
    try:
        return extract_test_commands_from_text(
            path.read_text(encoding="utf-8"),
            section=section,
        )
    except OSError:
        return []


def collect_test_commands_for_assert(
    cwd: str | Path,
    result: dict[str, Any],
    *,
    step_path: str | None = None,
) -> list[str]:
    """Prefer result.test_commands; else pytest_commands; else step tests:/## Тесты."""
    root = Path(cwd)
    out: list[str] = []
    seen: set[str] = set()
    for key in ("test_commands", "pytest_commands"):
        raw = result.get(key)
        if not isinstance(raw, list) or not raw:
            continue
        for c in raw:
            if isinstance(c, str):
                _add_test_cmd(c, seen, out)
        if out:
            return out[:5]

    if not step_path:
        return []
    path = root / step_path
    cmds = extract_test_commands_from_file(path, section="## Тесты")
    if cmds:
        return cmds[:5]
    return extract_test_commands_from_file(path, section=None)[:5]


def collect_pytest_commands_for_assert(
    cwd: str | Path,
    result: dict[str, Any],
    *,
    step_path: str | None = None,
) -> list[str]:
    return [
        cmd
        for cmd in collect_test_commands_for_assert(
            cwd, result, step_path=step_path
        )
        if cmd.startswith(_PYTEST_PREFIX)
    ][:3]


def pytest_assert_enabled() -> bool:
    raw = (os.environ.get("LOOP_ASSERT_PYTEST") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def run_test_commands(
    cwd: str | Path,
    commands: list[str],
    *,
    timeout_sec: int = 180,
) -> list[str]:
    """Run targeted pytest/vitest/tsc; return error strings (empty = all green)."""
    errors: list[str] = []
    root = Path(cwd)
    frontend = root / "frontend"
    for cmd in commands[:5]:
        cmd = normalize_test_command_entry(cmd)
        if not is_allowed_test_command(cmd):
            errors.append(f"refused command: {cmd!r}")
            continue
        try:
            if cmd.startswith(_PYTEST_PREFIX):
                args = shlex.split(cmd)
                proc = subprocess.run(
                    args,
                    cwd=str(root),
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    check=False,
                )
            elif cmd.startswith("cd frontend &&"):
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=str(root),
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    check=False,
                )
            elif cmd.startswith("npm exec"):
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=str(frontend),
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    check=False,
                )
            else:
                errors.append(f"refused command: {cmd!r}")
                continue
        except subprocess.TimeoutExpired:
            errors.append(f"timeout ({timeout_sec}s): {cmd}")
            continue
        except OSError as exc:
            errors.append(f"exec failed {cmd}: {exc}")
            continue
        if proc.returncode != 0:
            tail = (proc.stdout or "")[-800:] + (proc.stderr or "")[-400:]
            errors.append(f"{cmd} exit={proc.returncode}\n{tail.strip()}")
    return errors


def run_pytest_commands(
    cwd: str | Path,
    commands: list[str],
    *,
    timeout_sec: int = 180,
) -> list[str]:
    """Run targeted pytest only; return error strings (empty = all green)."""
    pytest_cmds = [cmd for cmd in commands if cmd.startswith(_PYTEST_PREFIX)]
    return run_test_commands(cwd, pytest_cmds, timeout_sec=timeout_sec)


def render_result_template(
    *,
    status: str = "ok",
    verdict: str | None = None,
    step_id: str | None = None,
    mode: str | None = None,
) -> str:
    """YAML snippet for agent prompt / docs."""
    v = "null" if verdict is None else verdict
    sid = step_id or "sNN"
    mode_s = mode or "IMPLEMENT"
    return (
        "version: 1\n"
        f"status: {status}          # ok | blocked | fail | halt | gaps (NOT pending)\n"
        "draft: false\n"
        f"verdict: {v}       # pass | blocked | fail | null (QA)\n"
        f"step_id: {sid}\n"
        "artifact: null     # path to step/qa shard\n"
        "role: null\n"
        f"mode: {mode_s}     # mode этой сессии, не next\n"
        "target: null       # optional @sNN / CR-*\n"
        "pytest_commands: null  # optional list of .venv/bin/pytest …\n"
        "test_commands: null   # optional pytest | vitest | tsc commands\n"
        "notes: null\n"
    )
