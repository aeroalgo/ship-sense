from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EPIC_LIB_PATH = ROOT / ".claude" / "hooks" / "epic_lib.py"
_HOOKS = str(ROOT / ".claude" / "hooks")
_TRANSITIONS = ROOT / "loop" / "transitions.yaml"
if _HOOKS not in sys.path:
    sys.path.insert(0, _HOOKS)


def _load_epic_lib():
    spec = importlib.util.spec_from_file_location("epic_lib", EPIC_LIB_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_back_implement_yaml(
    rel_path: str,
    cwd: Path,
    *,
    step_id: str = "s01",
    plan_id: str = "x",
    status: str = "completed",
) -> str:
    import yaml

    data = {
        "schema": "epic-implement/v1",
        "role": "back",
        "step_id": step_id,
        "plan_id": plan_id,
        "title": f"{step_id} demo IMPLEMENT",
        "status": status,
        "decompose_ref": f"memory-bank/back/plan/decompose-{plan_id}/{Path(rel_path).stem}.yaml",
        "implement_index": f"memory-bank/back/implement/implement-{plan_id}/index.md",
        "date": "2026-07-31",
        "level": "L2",
        "done": ["x"],
        "files": ["a.py"],
        "tests": ["cmd: `.venv/bin/pytest a -q`", "итог: 1 passed"],
        "integration_check": ["ok"],
        "checkpoints": [
            {
                "id": "cp1",
                "criterion": "step AC complete",
                "status": "done" if status == "completed" else "pending",
                "done_at": "2026-08-01" if status == "completed" else None,
            }
        ],
    }
    path = cwd / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return rel_path


def _write(rel_path: str, body: str, cwd: Path) -> str:
    path = cwd / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return rel_path


def _seed_loop(cwd: Path) -> None:
    loop_dir = cwd / "loop"
    loop_dir.mkdir(parents=True, exist_ok=True)
    loop_dir.joinpath("transitions.yaml").write_text(
        _TRANSITIONS.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def _write_result(cwd: Path, data: dict) -> None:
    import yaml

    path = cwd / "loop" / "runtime" / "epic" / "result.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_build_prompt_implement_packs_verify_contract(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    import yaml

    step_yaml = tmp_path / "memory-bank/back/plan/decompose-demo/s01-demo.yaml"
    step_yaml.parent.mkdir(parents=True, exist_ok=True)
    step_yaml.write_text(
        yaml.safe_dump(
            {
                "schema": "epic-decompose/v1",
                "role": "back",
                "step_id": "s01",
                "plan_id": "demo",
                "title": "s01 demo",
                "next_phase": "BACK IMPLEMENT",
                "needs_creative": "no",
                "goal": "demo",
                "checkpoints": [{"id": "cp1", "criterion": "ac"}],
                "verify": ["`.venv/bin/pytest tests/storage/test_demo.py -q`"],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    qa = _write(
        "memory-bank/back/qa/qa-demo/qa-20260801-demo.yaml",
        "schema: epic-qa/v1\n",
        tmp_path,
    )

    prompt = epic_lib.build_prompt(
        "BACK IMPLEMENT",
        tmp_path,
        [qa, str(step_yaml.relative_to(tmp_path))],
    )

    assert "## path-rule IMPLEMENT step (HARD)" in prompt
    assert "## spawn (pointer)" in prompt
    assert "spawn-hard.md" in prompt
    assert ".venv/bin/pytest tests/storage/test_demo.py -q" in prompt
    assert "\nAC+:\n" not in prompt
    assert "## spawn-gate IMPLEMENT" not in prompt


def test_build_prompt_refactor_packs_verify_contract(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    step = _write(
        "memory-bank/back/refactor/plan/decompose-demo/r01-demo.md",
        "# r01\n\n- `.venv/bin/pytest tests/storage/test_refactor.py -q`\n",
        tmp_path,
    )

    prompt = epic_lib.build_prompt("BACK REFACTOR", tmp_path, [step])

    assert "## path-rule REFACTOR epic (HARD)" in prompt
    assert "## spawn (pointer)" in prompt
    assert "Behavior freeze" in prompt
    assert "spawn-hard.md" in prompt
    assert ".venv/bin/pytest tests/storage/test_refactor.py -q" in prompt
    assert "## spawn-gate REFACTOR" not in prompt
    assert "\nAC+:\n" not in prompt


def test_parse_next_command_refactor_and_modes(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    handoff = (
        "## Handoff BACK REFACTOR — r01 done\n"
        "- **Следующий:** BACK REFACTOR @r02\n"
    )
    assert epic_lib.parse_next_command(handoff) == "BACK REFACTOR"
    assert epic_lib.command_mode("BACK REFACTOR") == "REFACTOR"
    assert epic_lib.command_mode("BACK REFACTOR PLAN") == "REFACTOR PLAN"
    assert epic_lib.command_mode("FRONT REFACTOR DECOMPOSE") == "REFACTOR DECOMPOSE"
    assert "REFACTOR" in epic_lib.ALLOWED_DEFAULT


def test_normalize_and_pending_refactor_decompose(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    _write(
        "memory-bank/back/refactor/plan/decompose-rf-demo/index.md",
        "| Step | Status |\n| --- | --- |\n| **r01** | done |\n| **r02** | pending |\n",
        tmp_path,
    )
    ref = epic_lib.normalize_decompose_ref(tmp_path, "decompose-rf-demo")
    assert ref.endswith("memory-bank/back/refactor/plan/decompose-rf-demo/index.md")
    assert epic_lib.is_refactor_decompose(tmp_path, ref) is True
    assert epic_lib.decompose_pending_left(tmp_path, ref) == 1


def test_resolve_next_refactor_bootstrap(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    _write(
        "memory-bank/back/refactor/plan/decompose-rf-boot/index.md",
        "| Step | Status |\n| --- | --- |\n| **r01** | pending |\n",
        tmp_path,
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/back/refactor/plan/decompose-rf-boot/index.md`\n\n"
        "## Handoff BACK\n- bootstrap\n",
        tmp_path,
    )
    epic_lib.arm_epic(tmp_path, "decompose-rf-boot", role_prefix="BACK")
    resolved = epic_lib.resolve_next(tmp_path)
    assert resolved["ok"] is True
    assert resolved["command"] == "BACK REFACTOR"
    assert "## path-rule REFACTOR epic (HARD)" in (resolved["prompt"] or "")
    assert "spawn-hard.md" in (resolved["prompt"] or "")


def test_build_prompt_bugfix_packs_verify_contract(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    bugfix = _write(
        "memory-bank/back/bugfix/bugfix-demo.md",
        "# bugfix\n\n- `.venv/bin/pytest tests/storage/test_bugfix.py -q`\n",
        tmp_path,
    )

    prompt = epic_lib.build_prompt("BACK BUGFIX", tmp_path, [bugfix])

    assert "## BUGFIX (HARD)" in prompt
    assert "spawn-hard.md" in prompt
    assert ".venv/bin/pytest tests/storage/test_bugfix.py -q" in prompt
    assert "transitions.yaml" in prompt
    assert "## spawn-gate BUGFIX" not in prompt
    assert "\nAC+:\n" not in prompt


def test_build_prompt_qa_packs_reviewer_contract(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    qa = _write("memory-bank/back/qa/qa-demo/qa-20260801-demo.yaml", "schema: x\n", tmp_path)
    step = _write("memory-bank/back/implement/implement-demo/s01-demo.yaml", "schema: x\n", tmp_path)

    prompt = epic_lib.build_prompt("BACK QA", tmp_path, [qa, step])

    assert "## BACK QA (HARD)" in prompt
    assert "epic-qa/v1" in prompt
    assert "templates/qa/epic-step.yaml" in prompt
    assert "@reviewer" in prompt
    assert "spawn-hard.md" in prompt
    assert "transitions.yaml" in prompt
    assert "## spawn-gate BACK QA" not in prompt
    assert "\nSuite results:\n" not in prompt
    assert "\nAC+:\n" not in prompt


def test_build_prompt_refactor_requires_yaml_template(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    prompt = epic_lib.build_prompt("BACK REFACTOR", tmp_path, [])
    assert "epic-refactor/v1" in prompt
    assert "templates/refactor/epic-step.yaml" in prompt


def _write_qa_yaml(tmp_path: Path, rel: str, *, verdict: str = "pass") -> str:
    import yaml

    data = {
        "schema": "epic-qa/v1",
        "role": "back",
        "date": "2026-08-01",
        "reviewer": "BACK QA",
        "verdict": verdict,
        "scope": ["epic: demo"],
        "checks": ["pytest green"],
        "issues": [],
        "blockers": [],
        "fix_plan": [],
        "plan_id": "demo",
    }
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return rel


def _write_refactor_yaml(tmp_path: Path, rel: str) -> str:
    import yaml

    data = {
        "schema": "epic-refactor/v1",
        "role": "back",
        "step_id": "r01",
        "plan_id": "rf-demo",
        "title": "r01 demo",
        "status": "completed",
        "date": "2026-08-01",
        "behavior_freeze": "API unchanged",
        "done": ["moved models"],
        "files": ["apps/api/app/models.py"],
        "tests": ["`.venv/bin/pytest tests/storage -q`"],
        "checkpoints": [{"id": "cp1", "criterion": "done", "status": "done"}],
    }
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return rel


def _write_decompose_yaml(tmp_path: Path, rel: str) -> str:
    import yaml

    data = {
        "schema": "epic-decompose/v1",
        "role": "back",
        "step_id": "s01",
        "plan_id": "demo",
        "title": "s01",
        "next_phase": "BACK IMPLEMENT",
        "needs_creative": "no",
        "goal": "goal",
        "checkpoints": [{"id": "cp1", "criterion": "ac"}],
    }
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return rel


def test_validate_qa_yaml_accepts_pass(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    rel = _write_qa_yaml(tmp_path, "memory-bank/back/qa/demo/qa-20260801-demo.yaml")
    assert epic_lib.validate_qa_shard(tmp_path / rel, "pass") == []


def test_validate_qa_yaml_rejects_md(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    path = tmp_path / "qa.md"
    path.write_text("# qa\n", encoding="utf-8")
    errs = epic_lib.validate_qa_shard(path, "pass")
    assert any(".yaml" in e for e in errs)


def test_crosscheck_qa_verdict_mismatch(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    rel = _write_qa_yaml(tmp_path, "memory-bank/back/qa/demo/qa-20260801-demo.yaml", verdict="pass")
    result = {"status": "ok", "verdict": "pass", "artifact": rel}
    assert (
        epic_lib.crosscheck_ok_result(
            tmp_path,
            result,
            last_mode="QA",
            decompose=None,
            step_path=rel,
            handoff="",
            verify_verdict=None,
        )
        == []
    )

    rel_fail = _write_qa_yaml(
        tmp_path,
        "memory-bank/back/qa/demo/qa-20260801-demo-fail.yaml",
        verdict="fail",
    )
    result_fail = {"status": "fail", "verdict": "fail", "artifact": rel_fail}
    errs = epic_lib.crosscheck_ok_result(
        tmp_path,
        result_fail,
        last_mode="QA",
        decompose=None,
        step_path=rel_fail,
        handoff="",
        verify_verdict=None,
    )
    assert any("fix_plan" in e for e in errs)


def test_crosscheck_decompose_on_finish(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    rel = _write_decompose_yaml(
        tmp_path, "memory-bank/back/plan/decompose-demo/s01-demo.yaml"
    )
    result = {"status": "ok", "mode": "DECOMPOSE", "step_id": "s01", "artifact": rel}
    assert epic_lib.crosscheck_ok_result(
        tmp_path,
        result,
        last_mode="DECOMPOSE",
        decompose="decompose-demo",
        step_path=rel,
        handoff="",
        verify_verdict=None,
    ) == []


def test_validate_refactor_yaml_accepts_canonical(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    rel = _write_refactor_yaml(
        tmp_path,
        "memory-bank/back/refactor/implement/implement-rf-demo/r01-demo.yaml",
    )
    assert epic_lib.validate_refactor_step_format(tmp_path / rel) == []


def test_coerce_qa_md_to_yaml_in_load_now() -> None:
    epic_lib = _load_epic_lib()
    text = (
        "## load_now\n"
        "- `memory-bank/back/qa/v1-p1-api/qa-20260731-v1-p1-api.md`\n"
    )
    paths = epic_lib.extract_load_now(text)
    assert paths[0].endswith(".yaml")


def test_parse_next_command_epic_qa_and_title_arrow() -> None:
    epic_lib = _load_epic_lib()
    handoff = (
        "## Handoff — BACK IMPLEMENT s10 → BACK QA v1-p1-api\n"
        "- **Epic QA:** `BACK QA v1-p1-api` — suite\n"
    )
    assert epic_lib.parse_next_command(handoff) == "BACK QA"

    handoff2 = (
        "## Handoff BACK QA — pass\n"
        "- **Следующий:** BACK REFLECT\n"
    )
    assert epic_lib.parse_next_command(handoff2) == "BACK REFLECT"


def test_resolve_next_pending0_advances_to_qa(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    _write(
        "memory-bank/back/plan/decompose-done-demo/index.md",
        "| Step | Status |\n| --- | --- |\n| **s01** | completed |\n",
        tmp_path,
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n"
        "- `memory-bank/back/plan/decompose-done-demo/index.md`\n\n"
        "## Handoff — BACK IMPLEMENT s01 → BACK QA\n"
        "- **Epic QA:** `BACK QA done-demo`\n",
        tmp_path,
    )
    epic_lib.arm_epic(tmp_path, "decompose-done-demo", role_prefix="BACK")
    resolved = epic_lib.resolve_next(tmp_path)
    assert resolved["ok"] is True
    assert resolved["command"] == "BACK QA"
    assert "## BACK QA (HARD)" in (resolved["prompt"] or "")
    assert "transitions.yaml" in (resolved["prompt"] or "")


def test_resolve_next_reflect_then_complete_before_archive(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    _seed_loop(tmp_path)
    _write(
        "memory-bank/back/plan/decompose-reflect-demo/index.md",
        "| Step | Status |\n| --- | --- |\n| **s01** | completed |\n",
        tmp_path,
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n"
        "- `memory-bank/back/plan/decompose-reflect-demo/index.md`\n\n"
        "## Handoff BACK QA — pass\n"
        "- **Следующий:** BACK REFLECT\n",
        tmp_path,
    )
    epic_lib.arm_epic(tmp_path, "decompose-reflect-demo", role_prefix="BACK")
    resolved = epic_lib.resolve_next(tmp_path)
    assert resolved["ok"] is True
    assert resolved["command"] == "BACK REFLECT"
    assert "## REFLECT" in (resolved["prompt"] or "")

    reflection = _write(
        "memory-bank/back/reflection/reflection-reflect-demo.md",
        "# REFLECT reflect-demo\n\n**Статус:** completed\n\n"
        "## Сравнение\n\n- ok\n\n## Что сработало\n\n- ok\n\n## Уроки\n\n- ok\n",
        tmp_path,
    )
    _write_result(
        tmp_path,
        {
            "version": 1,
            "status": "ok",
            "draft": False,
            "mode": "REFLECT",
            "role": "BACK",
            "artifact": reflection,
        },
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n"
        "- `memory-bank/back/plan/decompose-reflect-demo/index.md`\n\n"
        "## Handoff BACK REFLECT — done\n"
        f"- **Артефакт:** `{reflection}`\n"
        "- **Следующий:** BACK ARCHIVE NOW\n",
        tmp_path,
    )
    after = epic_lib.after_session(tmp_path)
    assert after["status"] == "complete"
    assert "ARCHIVE" in (after.get("reason") or "")

    # resolve must not run ARCHIVE — complete before
    st = epic_lib.load_epic_state(tmp_path)
    st["active"] = True
    st["status"] = "running"
    epic_lib.save_epic_state(tmp_path, st)
    resolved2 = epic_lib.resolve_next(tmp_path)
    assert resolved2["ok"] is False
    assert resolved2["status"] == "complete"
    assert resolved2["command"] == "BACK ARCHIVE NOW"


def test_decompose_pending_ignores_stale_checklist_when_table_done(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    _write(
        "memory-bank/back/plan/decompose-checklist-trap/index.md",
        "| step_id | status |\n| --- | --- |\n"
        "| **s01** | done |\n| **s02** | completed |\n\n"
        "## Summary\n- [ ] s01\n- [ ] s02\n",
        tmp_path,
    )
    ref = epic_lib.normalize_decompose_ref(tmp_path, "decompose-checklist-trap")
    assert epic_lib.decompose_pending_left(tmp_path, ref) == 0


def test_build_prompt_reflect_forbids_archive(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    prompt = epic_lib.build_prompt("BACK REFLECT", tmp_path, [])
    assert "## REFLECT" in prompt
    assert "BACK ARCHIVE NOW" in prompt
    assert "FORBIDDEN: ARCHIVE NOW" in prompt
    assert "REFLECT" in epic_lib.ALLOWED_DEFAULT


def test_build_prompt_implement_requires_step_template(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    prompt = epic_lib.build_prompt("BACK IMPLEMENT", tmp_path, [])
    assert "## path-rule IMPLEMENT step (HARD)" in prompt
    assert "templates/implement/epic-step.yaml" in prompt
    assert "epic-implement/v1" in prompt


def test_validate_implement_step_format_accepts_canonical(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    path = tmp_path / "s01-demo.yaml"
    _write_back_implement_yaml("s01-demo.yaml", tmp_path, step_id="s01", plan_id="demo")
    assert epic_lib.validate_implement_step_format(path) == []


def test_validate_implement_step_format_rejects_md(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    path = tmp_path / "s01-bad.md"
    path.write_text("# BACK IMPLEMENT s01\n", encoding="utf-8")
    errs = epic_lib.validate_implement_step_format(path)
    assert errs
    assert any(".yaml" in e for e in errs)


def test_validate_implement_step_format_rejects_integ_md(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    path = tmp_path / "e03-session-create-logout.md"
    path.write_text("# e03 IMPLEMENT\n", encoding="utf-8")
    errs = epic_lib.validate_implement_step_format(path)
    assert errs
    assert any(".yaml" in e for e in errs)


def test_validate_integ_implement_yaml_accepts_canonical(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    import yaml

    data = {
        "schema": "epic-implement/v1",
        "step_id": "e03",
        "plan_id": "v1-portal",
        "title": "e03 demo",
        "status": "completed",
        "element_ref": "memory-bank/integration/plan/decompose-v1-portal/e03.yaml",
        "implement_index": "memory-bank/integration/implement/implement-v1-portal/index.md",
        "date": "2026-08-01",
        "gaps": {"status": "none"},
        "grep_control": [{"back": "api/x", "front": "frontend/y"}],
        "verification_results": ["ok"],
        "checkpoints": [{"id": "cp1", "criterion": "wire", "status": "done"}],
    }
    path = tmp_path / "e03-session-create-logout.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    assert epic_lib.validate_implement_step_format(path) == []


def test_validate_integ_implement_yaml_rejects_grep_control_suffix(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    import yaml

    data = {
        "schema": "epic-implement/v1",
        "step_id": "e03",
        "plan_id": "v1-portal",
        "title": "e03 bad",
        "status": "completed",
        "element_ref": "x",
        "implement_index": "memory-bank/integration/implement/implement-v1-portal/index.md",
        "date": "2026-08-01",
        "gaps": {"status": "none"},
        "grep_control": [],
        "verification_results": ["ok"],
        "checkpoints": [{"id": "cp1", "criterion": "x", "status": "done"}],
    }
    path = tmp_path / "e03-bad.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    errs = epic_lib.validate_implement_step_format(path)
    assert any("grep_control" in e for e in errs)


def test_build_prompt_integr_implement_requires_integ_step_template(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    prompt = epic_lib.build_prompt("INTEG IMPLEMENT", tmp_path, [])
    assert "epic-step.yaml" in prompt
    assert "epic-implement/v1" in prompt
    assert "checkpoints" in prompt
    assert "templates/implement/step.md" not in prompt


def test_validate_integ_implement_yaml_accepts_canonical(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    import yaml

    data = {
        "schema": "epic-implement/v1",
        "step_id": "e03",
        "plan_id": "demo",
        "title": "e03 demo",
        "status": "completed",
        "element_ref": "memory-bank/integration/plan/decompose-demo/e03.yaml",
        "implement_index": "memory-bank/integration/implement/implement-demo/index.md",
        "date": "2026-08-01",
        "gaps": {"status": "none"},
        "grep_control": [{"back": "api/x", "front": "frontend/y"}],
        "verification_results": ["ok"],
        "checkpoints": [
            {
                "id": "cp1",
                "criterion": "wire",
                "status": "done",
                "done_at": "2026-08-01",
            }
        ],
        "resume_from": None,
    }
    path = tmp_path / "e03-demo.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    assert epic_lib.validate_implement_step_format(path) == []


def test_validate_integ_implement_yaml_rejects_pending_checkpoint(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    import yaml

    data = {
        "schema": "epic-implement/v1",
        "step_id": "e05",
        "plan_id": "demo",
        "title": "e05 demo",
        "status": "completed",
        "element_ref": "x",
        "implement_index": "memory-bank/integration/implement/implement-demo/index.md",
        "date": "2026-08-01",
        "gaps": {"status": "none"},
        "grep_control": [{"back": "a", "front": "b"}],
        "verification_results": ["ok"],
        "checkpoints": [
            {"id": "cp1", "criterion": "a", "status": "done"},
            {"id": "cp2", "criterion": "b", "status": "pending"},
        ],
    }
    path = tmp_path / "e05-demo.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    errs = epic_lib.validate_implement_step_format(path)
    assert any("cp2" in e for e in errs)


def test_resolve_expected_implement_step_integ_prefers_yaml(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    rel = epic_lib.resolve_expected_implement_step(
        tmp_path,
        ["memory-bank/integration/plan/decompose-v1-portal/e05-statusbar-alarms.yaml"],
        decompose="decompose-v1-portal",
        role="INTEG",
    )
    assert rel == (
        "memory-bank/integration/implement/implement-v1-portal/e05-statusbar-alarms.yaml"
    )


def test_reconcile_remaining_skips_completed_implement_yaml(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    import yaml

    _write(
        "memory-bank/integration/plan/decompose-v1-portal/index.md",
        "| step | status |\n| --- | --- |\n| **e01** | pending |\n| **e02** | pending |\n",
        tmp_path,
    )
    data = {
        "schema": "epic-implement/v1",
        "step_id": "e01",
        "plan_id": "v1-portal",
        "title": "e01",
        "status": "completed",
        "element_ref": "x",
        "implement_index": "memory-bank/integration/implement/implement-v1-portal/index.md",
        "date": "2026-08-01",
        "gaps": {"status": "none"},
        "grep_control": [{"back": "a", "front": "b"}],
        "verification_results": ["ok"],
        "checkpoints": [{"id": "cp1", "criterion": "x", "status": "done"}],
    }
    impl = tmp_path / "memory-bank/integration/implement/implement-v1-portal/e01-home-redirect.yaml"
    impl.parent.mkdir(parents=True, exist_ok=True)
    impl.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    remaining = [{"id": "e01", "next_phase": "IMPLEMENT"}, {"id": "e02", "next_phase": "IMPLEMENT"}]
    out = epic_lib.reconcile_remaining_with_implement(
        tmp_path, "memory-bank/integration/plan/decompose-v1-portal/index.md", remaining
    )
    assert [r["id"] for r in out] == ["e02"]


def test_resolve_expected_implement_step_from_decompose(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    rel = epic_lib.resolve_expected_implement_step(
        tmp_path,
        ["memory-bank/back/plan/decompose-v1-p2-ship/s04-b12-templates.md"],
        decompose="decompose-v1-p2-ship",
        role="BACK",
    )
    assert rel == "memory-bank/back/implement/implement-v1-p2-ship/s04-b12-templates.yaml"


def test_resolve_expected_implement_step_first_of_multiple(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    rel = epic_lib.resolve_expected_implement_step(
        tmp_path,
        [
            "memory-bank/back/plan/decompose-v1-p2-ship/s08-mnemo-bindings-loader.md",
            "memory-bank/back/plan/decompose-v1-p2-ship/s09-api-mnemo-endpoints.md",
            "memory-bank/back/plan/decompose-v1-p2-ship/index.md",
        ],
        decompose="memory-bank/back/plan/decompose-v1-p2-ship/index.md",
        role="BACK",
    )
    assert rel == (
        "memory-bank/back/implement/implement-v1-p2-ship/s08-mnemo-bindings-loader.yaml"
    )


def test_after_session_prefers_handoff_artifact_over_wrong_pending(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    _seed_loop(tmp_path)
    _write(
        "memory-bank/back/plan/decompose-v1-p2-ship/index.md",
        "| Step | Status |\n| --- | --- |\n"
        "| **s08** | completed |\n| **s09** | pending |\n",
        tmp_path,
    )
    _write_back_implement_yaml(
        "memory-bank/back/implement/implement-v1-p2-ship/s08-mnemo-bindings-loader.yaml",
        tmp_path,
        step_id="s08",
        plan_id="v1-p2-ship",
    )
    before_ctx = (
        "## load_now\n"
        "1. [s08](back/plan/decompose-v1-p2-ship/s08-mnemo-bindings-loader.md)\n"
        "2. [s09](back/plan/decompose-v1-p2-ship/s09-api-mnemo-endpoints.md)\n\n"
        "## Handoff BACK CREATIVE\n"
        "- **Следующий:** `BACK IMPLEMENT` @s08\n"
    )
    _write("memory-bank/activeContext.md", before_ctx, tmp_path)
    epic_lib.arm_epic(tmp_path, "decompose-v1-p2-ship", role_prefix="BACK")
    st = epic_lib.load_epic_state(tmp_path)
    st["active"] = True
    st["status"] = "running"
    st["last_command"] = "BACK IMPLEMENT"
    st["pending_fingerprint_before"] = epic_lib.fingerprint_context(before_ctx)
    st["pending_implement_step"] = (
        "memory-bank/back/implement/implement-v1-p2-ship/s09-api-mnemo-endpoints.yaml"
    )
    epic_lib.save_epic_state(tmp_path, st)

    after_ctx = (
        "## load_now\n"
        "1. [s09](back/plan/decompose-v1-p2-ship/s09-api-mnemo-endpoints.md)\n"
        "2. [index](back/plan/decompose-v1-p2-ship/index.md)\n\n"
        "## Handoff BACK IMPLEMENT s08\n"
        "- **Артефакт:** [s08-mnemo-bindings-loader.md]"
        "(back/implement/implement-v1-p2-ship/s08-mnemo-bindings-loader.md)\n"
        "- **code_changed:** no\n"
        "- **Следующий:** `BACK IMPLEMENT` @s09\n"
    )
    _write("memory-bank/activeContext.md", after_ctx, tmp_path)
    _write_result(
        tmp_path,
        {
            "version": 1,
            "status": "ok",
            "draft": False,
            "mode": "IMPLEMENT",
            "role": "BACK",
            "step_id": "s08",
            "artifact": (
                "memory-bank/back/implement/implement-v1-p2-ship/"
                "s08-mnemo-bindings-loader.yaml"
            ),
        },
    )

    after = epic_lib.after_session(tmp_path)
    assert after["ok"] is True, after
    assert after["status"] in {"running", "complete"}
    assert "missing step file" not in (after.get("reason") or "")
    st2 = epic_lib.load_epic_state(tmp_path)
    assert st2.get("status") != "halted"


def test_extract_load_now_parses_markdown_links() -> None:
    epic_lib = _load_epic_lib()
    text = (
        "## load_now\n"
        "1. [s04-b12-templates.md](back/plan/decompose-v1-p2-ship/s04-b12-templates.md) — next\n"
        "2. [index.md](back/plan/decompose-v1-p2-ship/index.md)\n\n"
        "## Handoff\n"
    )
    paths = epic_lib.extract_load_now(text)
    assert paths[0] == "memory-bank/back/plan/decompose-v1-p2-ship/s04-b12-templates.yaml"
    assert paths[1] == "memory-bank/back/plan/decompose-v1-p2-ship/index.md"


def test_implement_step_from_handoff() -> None:
    epic_lib = _load_epic_lib()
    handoff = (
        "## Handoff BACK IMPLEMENT s04\n"
        "- **Артефакт:** [s04-b12-templates.md](back/implement/implement-v1-p2-ship/s04-b12-templates.md)\n"
        "- **Следующий:** `BACK IMPLEMENT` @s05\n"
    )
    assert (
        epic_lib.implement_step_from_handoff(handoff)
        == "memory-bank/back/implement/implement-v1-p2-ship/s04-b12-templates.yaml"
    )
