#!/usr/bin/env python3
"""Loop session prompt builder — extracted from epic_lib.

Dependencies injected by epic_lib (no circular import).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

# Injected by epic_lib
load_epic_state: Callable[..., dict[str, Any]]
resolve_expected_implement_step: Callable[..., str | None]
implement_step_format_lines: Callable[..., list[str]]
EPIC_RESULT_REPAIR_MAX_ATTEMPTS: int
command_mode: Callable[..., str | None]
is_integ_implement_step_path: Callable[..., bool]
ROLE_MODE_RE: Any
utc_now: Callable[[], str]
_normalize_mb_path: Callable[[str], str]
extract_step_basename: Callable[..., str | None]
epic_id_from_decompose_path: Callable[..., str]

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


_VERIFY_CMD_HINTS = (
    ".venv/bin/pytest ",
    "cd frontend && npm ",
    "npm exec vitest",
    "npm test",
    "npx vitest",
    "npx playwright",
    "npm exec playwright",
    "rg ",
)


def _looks_like_verify_cmd(cmd: str) -> bool:
    c = cmd.strip()
    if not c:
        return False
    return any(h in c for h in _VERIFY_CMD_HINTS)


def _extract_verify_commands(cwd: str | Path, load_now: list[str]) -> list[str]:
    """Collect verify commands from step/qa/decompose YAML (pytest + vitest + playwright)."""
    root = Path(cwd)
    commands: list[str] = []
    seen: set[str] = set()

    def add(cmd: str) -> None:
        cmd = cmd.strip()
        if cmd.startswith("- "):
            cmd = cmd[2:].strip()
        if cmd.startswith("`") and cmd.endswith("`"):
            cmd = cmd[1:-1].strip()
        if not cmd or cmd in seen:
            return
        if not _looks_like_verify_cmd(cmd):
            return
        seen.add(cmd)
        commands.append(cmd)

    def absorb_yaml(data: dict[str, Any]) -> None:
        for key in ("tests", "verification_results", "verify"):
            for item in data.get(key) or []:
                if isinstance(item, str):
                    add(item)
        for cp in data.get("checkpoints") or []:
            if isinstance(cp, dict) and isinstance(cp.get("verify"), str):
                add(cp["verify"])

    prioritized = sorted(
        load_now,
        key=lambda p: (
            0 if p.endswith((".yaml", ".yml")) else 1,
            0 if "/decompose-" in p.replace("\\", "/") else 1,
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
            import yaml as _yaml

            data = _yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError(f"expected mapping YAML: {rel_path}")
            absorb_yaml(data)
            for ref_key in ("decompose_ref", "element_ref"):
                ref = data.get(ref_key)
                if isinstance(ref, str) and ref.endswith((".yaml", ".yml")):
                    ref_p = root / ref
                    if not ref_p.is_file():
                        raise FileNotFoundError(
                            f"{rel_path}: {ref_key}={ref!r} не найден"
                        )
                    ref_data = _yaml.safe_load(ref_p.read_text(encoding="utf-8"))
                    if not isinstance(ref_data, dict):
                        raise ValueError(f"expected mapping YAML: {ref}")
                    absorb_yaml(ref_data)
            if commands:
                break
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not any(h in raw for h in _VERIFY_CMD_HINTS):
                continue
            line = raw.strip()
            if "`" in line:
                for part in re.findall(r"`([^`]+)`", line):
                    add(part)
            else:
                add(line)
        if commands:
            break
    return commands[:5]


def _verify_lines_for_mode(
    cwd: str | Path, load_now: list[str], *, mode: str
) -> list[str]:
    """VERIFY cmds for prompt. No placeholder — empty load_now → empty list; else require cmds."""
    cmds = _extract_verify_commands(cwd, load_now)
    if cmds:
        return cmds
    if not load_now:
        return []
    stepish = [
        p
        for p in load_now
        if p.endswith((".yaml", ".yml", ".md"))
        and Path(p).name != "index.md"
        and any(
            x in p.replace("\\", "/")
            for x in (
                "/decompose-",
                "/implement/",
                "/bugfix/",
                "/refactor/",
            )
        )
        and (
            re.search(r"/[sera]\d{2}(?:-|/|\.)", p.replace("\\", "/"))
            or "/bugfix/" in p.replace("\\", "/")
        )
    ]
    if not stepish:
        return []
    raise ValueError(
        f"{mode}: нет runnable verify cmds в {stepish} "
        "(нужен checkpoints[].verify | verify[] | tests с "
        ".venv/bin/pytest / vitest / playwright)"
    )


def _role_from_cmd(cmd: str) -> str:
    m = ROLE_MODE_RE.match(cmd.strip())
    return m.group(1).upper() if m else "BACK"


_SPAWN_POINTER = (
    "Spawn packed (explorer/verify/reviewer): `.claude/instructions/spawn-hard.md` "
    "+ UserPromptSubmit SPAWN_MAP — не дублировать секции AC+/ALLOW здесь."
)


def _resolve_decompose_for_step(
    cwd: str | Path,
    *,
    role_l: str,
    step_rel: str | None,
    load_now: list[str],
    doc: Any | None = None,
) -> Any:
    """Load EpicDecomposeDoc for current IMPLEMENT step. Raises if not found/invalid."""
    import epic_yaml as ey

    root = Path(cwd)
    candidates: list[Path] = []
    if doc is not None:
        for attr in ("decompose_ref", "element_ref"):
            ref = getattr(doc, attr, None)
            if isinstance(ref, str) and ref.strip():
                candidates.append(root / ref.strip())
    for p in load_now:
        if "/decompose-" in p.replace("\\", "/") and p.endswith((".yaml", ".yml")):
            candidates.append(root / p)
    if step_rel:
        st = load_epic_state(cwd)
        epic_id = epic_id_from_decompose_path(st.get("decompose") or "")
        if not epic_id:
            for p in load_now:
                m = re.search(r"decompose-([^/]+)", p.replace("\\", "/"))
                if m:
                    epic_id = m.group(1)
                    break
        if epic_id:
            dec_stem = Path(step_rel).stem
            sid_m = re.match(r"^([se]\d{2})", dec_stem.lower())
            step_key = sid_m.group(1) if sid_m else dec_stem.lower()
            candidates.append(
                root / ey.resolve_decompose_path(cwd, role_l, epic_id, step_key)
            )
    seen: set[str] = set()
    errors: list[str] = []
    for cand in candidates:
        key = str(cand)
        if key in seen:
            continue
        seen.add(key)
        if not cand.is_file():
            errors.append(f"missing: {cand}")
            continue
        return ey.load_decompose(cand)
    raise FileNotFoundError(
        "decompose shard не найден для step_context: "
        + ("; ".join(errors) if errors else "нет candidates")
    )


def _epic_checkpoint_appendix(
    cwd: str | Path, load_now: list[str], role: str
) -> list[str]:
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
        has_dec = any(
            "/decompose-" in p.replace("\\", "/") and p.endswith((".yaml", ".yml"))
            for p in load_now
        )
        if not has_dec:
            return []
        dec_only = _resolve_decompose_for_step(
            cwd, role_l=role_l, step_rel=None, load_now=load_now
        )
        lines = ey.step_context_prompt_lines(dec_only)
        import session_resilience as sr

        last = sr.load_last_session(cwd, track="epic")
        lines.extend(
            sr.dirty_resume_prompt_lines(
                cwd,
                step_id=dec_only.step_id,
                delta=list(dec_only.delta or []),
                resume_from=None,
                last=last,
            )
        )
        ok_paths, missing = sr.delta_paths_exist(cwd, list(dec_only.delta or []))
        if ok_paths and dec_only.delta:
            lines.extend(
                [
                    "",
                    "## explorer (HARD)",
                    "delta_paths_exist: yes — @explorer SKIP для этого шага.",
                    "FORBIDDEN: широкий codebase search / Agent explorer когда delta paths на диске.",
                ]
            )
        elif dec_only.delta and missing:
            lines.extend(
                [
                    "",
                    "## explorer (HARD)",
                    "delta_paths_exist: no — REQUIRED @explorer (packed).",
                    "missing: " + ", ".join(missing[:8]),
                ]
            )
        return lines

    doc = ey.find_implement_doc(cwd, step_rel)
    dec = _resolve_decompose_for_step(
        cwd, role_l=role_l, step_rel=step_rel, load_now=load_now, doc=doc
    )
    if doc is None:
        impl_p = Path(cwd) / step_rel
        impl_p.parent.mkdir(parents=True, exist_ok=True)
        seeded = ey.seed_implement_checkpoints(dec, None)
        epic_id = (dec.plan_id or "").strip()
        if not epic_id:
            raise ValueError(
                f"decompose {dec.step_id}: plan_id пуст — нельзя seed implement"
            )
        role_dir = ey.role_dir(role_l)
        dec_rel = None
        for p in load_now:
            if "/decompose-" in p.replace("\\", "/") and p.endswith((".yaml", ".yml")):
                dec_rel = p.replace("\\", "/")
                break
        if not dec_rel:
            raise ValueError(
                f"seed implement {step_rel}: нет decompose yaml в load_now"
            )
        data: dict[str, Any] = {
            "schema": ey.SCHEMA_EPIC_IMPLEMENT,
            "role": role_l,
            "step_id": dec.step_id,
            "plan_id": dec.plan_id,
            "title": dec.title,
            "status": "in_progress",
            "decompose_ref": dec_rel,
            "implement_index": f"memory-bank/{role_dir}/implement/implement-{epic_id}/index.md",
            "date": utc_now()[:10],
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

    lines = ey.checkpoint_prompt_lines(doc)
    lines.extend(ey.step_context_prompt_lines(dec, doc))

    # dirty resume + explorer skip (resilience)
    try:
        import session_resilience as sr

        last = sr.load_last_session(cwd, track="epic")
        resume = None
        if doc is not None:
            resume = doc.resume_from or ey.compute_resume_from(doc.checkpoints)
        lines.extend(
            sr.dirty_resume_prompt_lines(
                cwd,
                step_id=dec.step_id,
                delta=list(dec.delta or []),
                resume_from=resume,
                last=last,
            )
        )
        ok_paths, missing = sr.delta_paths_exist(cwd, list(dec.delta or []))
        if ok_paths and dec.delta:
            lines.extend(
                [
                    "",
                    "## explorer (HARD)",
                    "delta_paths_exist: yes — @explorer SKIP для этого шага.",
                    "FORBIDDEN: широкий codebase search / Agent explorer когда delta paths на диске.",
                    "ALLOWED: Read только dirty_files + paths из delta/as_built.",
                ]
            )
        elif dec.delta and missing:
            lines.extend(
                [
                    "",
                    "## explorer (HARD)",
                    "delta_paths_exist: no — missing: "
                    + ", ".join(missing[:8])
                    + ("…" if len(missing) > 8 else ""),
                    "REQUIRED: @explorer (packed) один раз до широкого search.",
                ]
            )
    except Exception as exc:
        raise RuntimeError(f"resume/explorer prompt failed: {exc}") from exc

    return lines


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
        verify_lines = _verify_lines_for_mode(cwd, load_now, mode="IMPLEMENT")
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
        out = [
            "",
            *extra,
            "",
            "## path-rule IMPLEMENT step (HARD)",
            *implement_step_format_lines(role=role_l, integ=integ),
            *artifact_hint,
            "Канон: finish-block.mdc · validator = loop after-hook "
            f"(до {EPIC_RESULT_REPAIR_MAX_ATTEMPTS}× RESULT REPAIR при FAIL).",
            "",
            "## Repair lanes (HARD — не путать)",
            "VERIFY loop (в сессии): Write step → finalize result → @verify → "
            "FAIL/DENY → fix → @verify → PASS → FINISH.",
            "RESULT REPAIR (после after): только docs/result format; "
            "FORBIDDEN @verify в repair-сессии.",
            "",
            "## spawn (pointer)",
            "code_changed=yes → @verify; codebase search → @explorer.",
        ]
        if verify_lines:
            out.append("VERIFY cmds (вставить в packed VERIFY:):")
            out.extend(f"- {line}" for line in verify_lines)
        out.append(_SPAWN_POINTER)
        return out

    if mode == "REFACTOR":
        verify_lines = _verify_lines_for_mode(cwd, load_now, mode="REFACTOR")
        role_l = role.strip().lower()
        out = [
            "",
            "## path-rule REFACTOR epic (HARD)",
            *(__import__("epic_shard_extra", fromlist=["refactor_format_spec_lines"]).refactor_format_spec_lines(role=role_l)),
            "`memory-bank/{role}/refactor/implement/implement-<id>/rNN-<slug>.yaml`",
            "FORBIDDEN: session-*.md в корне refactor/ при эпике; legacy `.md` rNN shard.",
            "Behavior freeze; один rNN за сессию. Канон: workflow-refactor-epic.mdc",
            "",
            "## spawn (pointer)",
            "code_changed=yes → @verify.",
        ]
        if verify_lines:
            out.append("VERIFY cmds:")
            out.extend(f"- {line}" for line in verify_lines)
        out.append(_SPAWN_POINTER)
        return out

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
        verify_lines = _verify_lines_for_mode(cwd, load_now, mode="BUGFIX")
        out = [
            "",
            "## BUGFIX (HARD)",
            "Root-cause fix (без fallback/hide) → targeted pytest → @verify если code_changed.",
        ]
        if verify_lines:
            out.append("VERIFY cmds:")
            out.extend(f"- {line}" for line in verify_lines)
        out.extend(
            [
                "Next-mode: `loop/transitions.yaml` (обычно → QA).",
                _SPAWN_POINTER,
            ]
        )
        return out

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
    appendix = _mode_appendix(cmd, cwd, load_now)
    # Task-first: mode appendix (step_context / checkpoints / Do) before process walls
    lines = [
        cmd,
        "",
        "## Do (task-first)",
        "Один atomic шаг из appendix ниже. Сначала goal/delta/checkpoints, потом FINISH.",
    ]
    if load_now:
        lines.append(f"load_now[0]: {load_now[0]}")
        for p in load_now[1:3]:
            lines.append(f"load_now: {p}")
    else:
        lines.append("load_now: shard из Handoff / decompose index (первый pending)")
    lines.extend(appendix)
    lines.extend(
        [
            "",
            "## Process (коротко)",
            "EPIC MODE: FINISH → Write весь activeContext.md "
            "(load_now → 1× ## Handoff → ≤1× ## done) + stop.",
            "Старт: 1) activeContext load_now+Handoff 2) ONE shard "
            "3) isolation `_lean/<mode>.mdc` — не весь workflow chain.",
            "FORBIDDEN: @verify после PASS; править loop-state.yaml; стопка Handoff; "
            "completed в load_now; следующий sNN в этой сессии; /exit|/clear.",
            "Next-mode: loop/transitions.yaml. Spawn: spawn-hard.md.",
            "## Repair lanes (HARD)",
            "VERIFY loop ≠ RESULT REPAIR (см. IMPLEMENT appendix / prepare-repair).",
        ]
    )
    return "\n".join(lines)

