#!/usr/bin/env python3
"""Result artifact crosscheck — extracted from epic_lib.

Dependencies injected by epic_lib (no circular import).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

# Injected by epic_lib at load time (resolved at call time)
handoff_code_changed_no: Callable[..., bool]
parse_next_command: Callable[..., str | None]
command_mode: Callable[..., str | None]
decompose_pending_left: Callable[..., int | None]
validate_implement_step_format: Callable[..., list[str]]
_decompose_index_path: Callable[..., Path | None]
_normalize_mb_path: Callable[[str], str]

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
            for step in sorted(
                list(idx.parent.glob("s*.yaml")) + list(idx.parent.glob("e*.yaml"))
            ):
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


