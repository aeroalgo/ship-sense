from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"
TRANSITIONS = ROOT / "loop" / "transitions.yaml"


def _write_back_implement_yaml(cwd: Path, rel: str, *, step_id: str = "s01") -> Path:
    import yaml

    data = {
        "schema": "epic-implement/v1",
        "role": "back",
        "step_id": step_id,
        "plan_id": "x",
        "title": f"{step_id} foo IMPLEMENT",
        "status": "completed",
        "decompose_ref": f"memory-bank/back/plan/decompose-x/{Path(rel).name}",
        "implement_index": "memory-bank/back/implement/implement-x/index.md",
        "date": "2026-07-31",
        "done": ["a"],
        "files": ["f.py"],
        "tests": ["cmd: pytest -q"],
        "integration_check": ["ok"],
        "checkpoints": [
            {"id": "cp1", "criterion": "step AC complete", "status": "done", "done_at": "2026-08-01"}
        ],
    }
    path = cwd / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _load(name: str):
    if str(HOOKS) not in sys.path:
        sys.path.insert(0, str(HOOKS))
    path = HOOKS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _seed_transitions(cwd: Path) -> None:
    sys_dir = cwd / "loop"
    sys_dir.mkdir(parents=True)
    sys_dir.joinpath("transitions.yaml").write_text(
        TRANSITIONS.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def test_transitions_file_loads():
    le = _load("loop_engine")
    tr = le.load_transitions(ROOT)
    assert "profiles" in tr
    assert "BACK" in tr["profiles"]
    assert "INTEG" in tr["profiles"]
    ids = [r["id"] for r in tr["transitions"]]
    assert "qa-pass-to-reflect" in ids
    assert "integ-gaps-open" in ids
    assert le.SYSTEM_DIR == "loop"


def test_apply_qa_pass(tmp_path: Path):
    le = _load("loop_engine")
    _seed_transitions(tmp_path)
    st = le.default_loop_state()
    st.update(
        {
            "active": True,
            "status": "running",
            "role": "BACK",
            "mode": "QA",
            "journey": {"id": None, "phase": "EPIC"},
            "epic": {"decompose": "x", "plan_id": "x", "pending": 0},
            "next": {"command": "BACK QA", "target": None},
        }
    )
    le.save_loop_state(tmp_path, st)
    r = le.apply_event(tmp_path, "finish_ok")
    assert r["ok"] is True
    assert r["transition"] == "qa-pass-to-reflect"
    assert r["state"]["mode"] == "REFLECT"
    assert r["state"]["next"]["command"] == "BACK REFLECT"


def test_apply_implement_pending(tmp_path: Path):
    le = _load("loop_engine")
    _seed_transitions(tmp_path)
    st = le.default_loop_state()
    st.update(
        {
            "active": True,
            "status": "running",
            "role": "BACK",
            "mode": "IMPLEMENT",
            "journey": {"id": None, "phase": "EPIC"},
            "epic": {"decompose": "x", "pending": 3},
            "next": {"command": "BACK IMPLEMENT", "target": "s02"},
        }
    )
    le.save_loop_state(tmp_path, st)
    r = le.apply_event(tmp_path, "finish_ok")
    assert r["ok"] is True
    assert r["transition"] == "implement-next-step"
    assert r["state"]["mode"] == "IMPLEMENT"


def test_sync_from_handoff(tmp_path: Path):
    le = _load("loop_engine")
    _seed_transitions(tmp_path)
    handoff = (
        "## Handoff BACK IMPLEMENT s07\n"
        "- **Следующий:** `BACK CREATIVE CR-P2-05` → затем `BACK IMPLEMENT` @s08\n"
    )
    st = le.sync_from_handoff(
        tmp_path,
        handoff,
        load_now=["memory-bank/back/plan/decompose-x/s08-y.md"],
        decompose="memory-bank/back/plan/decompose-x/index.md",
        pending=12,
        save=True,
    )
    assert st["role"] == "BACK"
    assert st["mode"] == "CREATIVE"
    assert st["next"]["command"] == "BACK CREATIVE"
    assert st["next"]["target"] == "CR-P2-05"
    assert st["epic"]["pending"] == 12
    assert (tmp_path / "loop" / "loop-state.yaml").is_file()


def test_qa_bugfix_loop_via_advance(tmp_path: Path):
    le = _load("loop_engine")
    _seed_transitions(tmp_path)
    st = le.default_loop_state()
    st.update(
        {
            "active": True,
            "status": "running",
            "role": "BACK",
            "mode": "QA",
            "journey": {"id": None, "phase": "EPIC"},
            "epic": {"decompose": "x", "pending": 0},
        }
    )
    le.save_loop_state(tmp_path, st)

    r1 = le.advance_ledger_after_session(
        tmp_path,
        last_mode="QA",
        handoff="## Handoff BACK QA — blocked\n- **Следующий:** BACK BUGFIX foo\n",
        role="BACK",
        pending=0,
        result={"version": 1, "status": "blocked", "verdict": "blocked", "mode": "QA"},
    )
    assert r1["ok"] is True
    assert r1["event"] == "finish_blocked"
    assert r1["state"]["mode"] == "BUGFIX"
    assert r1["state"]["next"]["command"] == "BACK BUGFIX"

    r2 = le.advance_ledger_after_session(
        tmp_path,
        last_mode="BUGFIX",
        handoff="## Handoff BACK BUGFIX\n- **Следующий:** BACK QA\n",
        role="BACK",
        pending=0,
        result={"version": 1, "status": "ok", "mode": "BUGFIX"},
    )
    assert r2["ok"] is True
    assert r2["event"] == "finish_ok"
    assert r2["state"]["mode"] == "QA"

    r3 = le.advance_ledger_after_session(
        tmp_path,
        last_mode="QA",
        handoff="## Handoff BACK QA — blocked\n- **Следующий:** BACK BUGFIX bar\n",
        role="BACK",
        pending=0,
        result={"version": 1, "status": "blocked", "verdict": "blocked", "mode": "QA"},
    )
    assert r3["state"]["mode"] == "BUGFIX"

    r4 = le.advance_ledger_after_session(
        tmp_path,
        last_mode="QA",
        handoff="## Handoff BACK QA — pass\n- **Следующий:** BACK REFLECT\n",
        role="BACK",
        pending=0,
        result={"version": 1, "status": "ok", "verdict": "pass", "mode": "QA"},
    )
    assert r4["event"] == "finish_ok"
    assert r4["state"]["mode"] == "REFLECT"
    assert r4["state"]["verdict"] == "pass"


def test_infer_requires_result():
    le = _load("loop_engine")
    assert (
        le.infer_finish_event(
            result={"version": 1, "status": "blocked", "verdict": "blocked"},
        )
        == "finish_blocked"
    )
    assert (
        le.infer_finish_event(
            result={"version": 1, "status": "gaps"},
        )
        == "gaps_found"
    )
    try:
        le.infer_finish_event(result=None)  # type: ignore[arg-type]
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_advance_rejects_missing_result(tmp_path: Path):
    le = _load("loop_engine")
    _seed_transitions(tmp_path)
    st = le.default_loop_state()
    st.update(
        {
            "active": True,
            "status": "running",
            "role": "BACK",
            "mode": "QA",
            "epic": {"decompose": "x", "pending": 0},
        }
    )
    le.save_loop_state(tmp_path, st)
    r = le.advance_ledger_after_session(
        tmp_path,
        last_mode="QA",
        handoff="## Handoff BACK QA — pass\n",
        role="BACK",
        pending=0,
        result=None,
    )
    assert r["ok"] is False
    assert "no handoff fallback" in (r.get("reason") or "")


def test_advance_with_result_yaml(tmp_path: Path):
    le = _load("loop_engine")
    sr = _load("session_result")
    _seed_transitions(tmp_path)
    st = le.default_loop_state()
    st.update(
        {
            "active": True,
            "status": "running",
            "role": "BACK",
            "mode": "QA",
            "journey": {"id": None, "phase": "EPIC"},
            "epic": {"decompose": "x", "pending": 0},
        }
    )
    le.save_loop_state(tmp_path, st)
    sr.save_result(
        tmp_path,
        {"status": "blocked", "verdict": "blocked", "mode": "QA", "role": "BACK"},
        track="epic",
    )
    result = sr.load_result(tmp_path, track="epic")
    r = le.advance_ledger_after_session(
        tmp_path,
        last_mode="QA",
        handoff="## Handoff BACK QA — pass\n- **Следующий:** BACK REFLECT\n",
        role="BACK",
        pending=0,
        result=result,
        track="epic",
    )
    assert r["ok"] is True
    assert r["event"] == "finish_blocked"
    assert r["result_source"] == "result.yaml"
    assert r["state"]["mode"] == "BUGFIX"
    trace = tmp_path / ".claude" / "runtime" / "epic" / "trace.jsonl"
    assert trace.is_file()
    assert "finish_blocked" in trace.read_text(encoding="utf-8")


def test_graph_check_ok():
    le = _load("loop_engine")
    report = le.validate_transitions_graph(ROOT)
    assert report["ok"] is True
    assert report["stats"]["transitions"] > 5
    mermaid = le.render_transitions_mermaid(ROOT)
    assert "stateDiagram-v2" in mermaid
    assert "QA --> BUGFIX" in mermaid or "QA --> REFLECT" in mermaid


def test_session_result_validate():
    sr = _load("session_result")
    assert sr.validate_result({"status": "ok"}) == []
    assert sr.validate_result({"status": "nope"})
    assert sr.validate_result({"status": "pending", "draft": True})
    assert not sr.is_finalized_result({"status": "pending", "draft": True})
    assert sr.is_finalized_result({"status": "ok", "draft": False})
    assert sr.event_from_result({"status": "fail"}) == "finish_fail"
    assert sr.event_from_result({"status": "ok", "verdict": "pass"}) == "finish_ok"
    assert any(
        "verdict" in e
        for e in sr.validate_result({"status": "ok", "mode": "QA", "draft": False})
    )
    assert sr.validate_result(
        {"status": "ok", "mode": "QA", "verdict": "pass", "draft": False}
    ) == []
    assert any(
        "incompatible" in e
        for e in sr.validate_result(
            {"status": "ok", "mode": "QA", "verdict": "blocked", "draft": False}
        )
    )


def test_session_result_normalize_status_pass_alias():
    sr = _load("session_result")
    data, changes = sr.normalize_result(
        {"status": "pass", "mode": "QA", "verdict": "pass", "draft": False}
    )
    assert data["status"] == "ok"
    assert data["verdict"] == "pass"
    assert changes
    assert sr.validate_result(data) == []

    data2, changes2 = sr.normalize_result(
        {"status": "pass", "mode": "QA", "draft": False}
    )
    assert data2["status"] == "ok"
    assert data2["verdict"] == "pass"
    assert changes2
    assert sr.validate_result(data2) == []

    data3, ch3 = sr.normalize_result(
        {"status": "ok", "mode": "QA", "verdict": "blocked", "draft": False}
    )
    assert data3["status"] == "blocked"
    assert "QA status" in ch3[0]
    assert sr.validate_result(data3) == []

    stub, stub_ch = sr.normalize_result({"status": "pending", "draft": True})
    assert stub["status"] == "pending"
    assert stub_ch == []


def test_load_and_normalize_persists(tmp_path: Path):
    sr = _load("session_result")
    sr.save_result(
        tmp_path,
        {
            "status": "pass",
            "mode": "QA",
            "verdict": "pass",
            "draft": False,
            "artifact": "memory-bank/back/qa/x.md",
        },
    )
    data, changes = sr.load_and_normalize_result(tmp_path, persist=True)
    assert changes
    assert data["status"] == "ok"
    reloaded = sr.load_result(tmp_path)
    assert reloaded["status"] == "ok"


def test_normalize_integ_artifact_md_to_yaml(tmp_path: Path):
    sr = _load("session_result")
    impl = (
        tmp_path
        / "memory-bank/integration/implement/implement-v1-portal/e04-appshell-chrome.yaml"
    )
    impl.parent.mkdir(parents=True, exist_ok=True)
    impl.write_text("schema: epic-implement/v1\n", encoding="utf-8")
    bad = (
        "memory-bank/integration/implement/implement-v1-portal/e04-appshell-chrome.md"
    )
    data, changes = sr.normalize_result(
        {"status": "ok", "mode": "IMPLEMENT", "draft": False, "artifact": bad},
        cwd=tmp_path,
    )
    assert data["artifact"].endswith(".yaml")
    assert changes
    assert "yaml canonical" in changes[0]


def test_prepare_result_repair_max_three(tmp_path: Path):
    el = _load("epic_lib")
    (tmp_path / "memory-bank/back/plan/decompose-r1").mkdir(parents=True)
    (tmp_path / "memory-bank/back/plan/decompose-r1/index.md").write_text(
        "| Step | Status |\n| --- | --- |\n| **s01** | completed |\n",
        encoding="utf-8",
    )
    (tmp_path / "memory-bank/activeContext.md").write_text(
        "## load_now\n- x\n\n## Handoff BACK QA\n- **Следующий:** BACK REFLECT\n",
        encoding="utf-8",
    )
    el.arm_epic(tmp_path, "decompose-r1", role_prefix="BACK")
    st = el.load_epic_state(tmp_path)
    st["active"] = False
    st["status"] = "halted"
    st["halt_reason"] = "result.yaml validate FAIL: status must be … got 'pass'"
    el.save_epic_state(tmp_path, st)

    for n in (1, 2, 3):
        r = el.prepare_result_repair(tmp_path)
        assert r["ok"] is True, n
        assert r["repair_attempt"] == n
        assert Path(r["prompt_file"]).is_file()
        body = Path(r["prompt_file"]).read_text(encoding="utf-8")
        assert "RESULT REPAIR" in body
        assert f"Попытка: {n}/3" in body

    r4 = el.prepare_result_repair(tmp_path)
    assert r4["ok"] is False
    assert "already attempted (3/3)" in r4["reason"]


def test_write_stub_and_extract_pytest(tmp_path: Path):
    sr = _load("session_result")
    path = sr.write_stub_result(
        tmp_path, role="BACK", mode="IMPLEMENT", step_id="s09"
    )
    assert path.is_file()
    data = sr.load_result(tmp_path)
    assert data["status"] == "pending"
    assert data["draft"] is True
    assert not sr.is_finalized_result(data)

    text = (
        "## Тесты\n"
        "- `.venv/bin/pytest apps/api/tests/mnemo -q`\n"
        "- other\n\n"
        "## Integration check\n"
        "- ok\n"
    )
    cmds = sr.extract_pytest_commands_from_text(text)
    assert cmds == [".venv/bin/pytest apps/api/tests/mnemo -q"]

    step = tmp_path / "step.md"
    step.write_text(text, encoding="utf-8")
    collected = sr.collect_pytest_commands_for_assert(
        tmp_path,
        {"status": "ok"},
        step_path="step.md",
    )
    assert collected == cmds


def test_run_test_commands_refuses_unknown(tmp_path: Path):
    sr = _load("session_result")
    errs = sr.run_test_commands(tmp_path, ["echo hi"])
    assert errs and "refused" in errs[0]


def test_collect_test_commands_from_integ_yaml(tmp_path: Path):
    sr = _load("session_result")
    import yaml

    step = tmp_path / "memory-bank/integration/implement/implement-v1-portal/e05.yaml"
    step.parent.mkdir(parents=True)
    step.write_text(
        yaml.safe_dump(
            {
                "schema": "epic-implement/v1",
                "role": "integ",
                "step_id": "e05",
                "tests": [
                    "`cd frontend && npm exec vitest -- run src/foo.test.tsx` — PASS",
                    "`npm exec tsc -- --noEmit` — PASS",
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    collected = sr.collect_test_commands_for_assert(
        tmp_path,
        {"status": "ok"},
        step_path=str(step.relative_to(tmp_path)),
    )
    assert collected == [
        "cd frontend && npm exec vitest -- run src/foo.test.tsx",
        "npm exec tsc -- --noEmit",
    ]


def test_collect_test_commands_prefers_result_test_commands(tmp_path: Path):
    sr = _load("session_result")
    collected = sr.collect_test_commands_for_assert(
        tmp_path,
        {
            "status": "ok",
            "test_commands": [
                "cd frontend && npm exec vitest -- run src/bar.test.tsx",
            ],
        },
        step_path=None,
    )
    assert collected == ["cd frontend && npm exec vitest -- run src/bar.test.tsx"]


def test_crosscheck_ok_requires_verify_pass(tmp_path: Path):
    el = _load("epic_lib")
    errs = el.crosscheck_ok_result(
        tmp_path,
        {"status": "ok", "mode": "IMPLEMENT", "step_id": "s01"},
        last_mode="IMPLEMENT",
        decompose=None,
        step_path=None,
        handoff="- **code_changed:** yes\n",
        verify_verdict="FAIL",
    )
    assert any("verify VERDICT: FAIL" in e for e in errs)

    errs2 = el.crosscheck_ok_result(
        tmp_path,
        {"status": "ok", "mode": "IMPLEMENT"},
        last_mode="IMPLEMENT",
        decompose=None,
        step_path=None,
        handoff="- **code_changed:** yes\n",
        verify_verdict=None,
    )
    assert any("требует verify VERDICT: PASS" in e for e in errs2)

    errs3 = el.crosscheck_ok_result(
        tmp_path,
        {"status": "ok", "mode": "IMPLEMENT"},
        last_mode="IMPLEMENT",
        decompose=None,
        step_path=None,
        handoff="- **code_changed:** no\n",
        verify_verdict=None,
    )
    # no step path still errors for IMPLEMENT; filter verify-only
    assert not any("verify" in e.lower() for e in errs3)


def test_crosscheck_qa_creative_reflect(tmp_path: Path):
    el = _load("epic_lib")

    qa = tmp_path / "memory-bank" / "back" / "qa" / "x" / "qa-20260731-x.yaml"
    qa.parent.mkdir(parents=True)
    import yaml

    qa.write_text(
        yaml.safe_dump(
            {
                "schema": "epic-qa/v1",
                "role": "back",
                "date": "2026-07-31",
                "reviewer": "BACK QA",
                "verdict": "pass",
                "scope": ["task: T-x"],
                "checks": ["ok"],
                "issues": [],
                "blockers": [],
                "fix_plan": [],
                "plan_id": "x",
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    rel_qa = str(qa.relative_to(tmp_path))
    errs = el.crosscheck_result_artifacts(
        tmp_path,
        {
            "status": "ok",
            "verdict": "pass",
            "mode": "QA",
            "artifact": rel_qa,
        },
        last_mode="QA",
        decompose=None,
        step_path=None,
        handoff=f"- **Артефакт:** [{rel_qa}]({rel_qa})\n",
        verify_verdict=None,
    )
    assert errs == []

    errs_bad = el.crosscheck_result_artifacts(
        tmp_path,
        {"status": "ok", "verdict": "blocked", "mode": "QA", "artifact": rel_qa},
        last_mode="QA",
        decompose=None,
        step_path=None,
        handoff="",
        verify_verdict=None,
    )
    assert any("несовместим" in e or "Verdict" in e for e in errs_bad)

    cr = (
        tmp_path
        / "memory-bank"
        / "back"
        / "creative"
        / "epic"
        / "creative-foo.md"
    )
    cr.parent.mkdir(parents=True)
    cr.write_text(
        "# BACK CREATIVE\n\n**Creative ID:** CR-T-01\n**Статус:** closed\n\n"
        "## Skills gate\n- a\n",
        encoding="utf-8",
    )
    rel_cr = str(cr.relative_to(tmp_path))
    errs_cr = el.crosscheck_result_artifacts(
        tmp_path,
        {"status": "ok", "mode": "CREATIVE", "artifact": rel_cr},
        last_mode="CREATIVE",
        decompose=None,
        step_path=None,
        handoff="- **Следующий:** BACK IMPLEMENT @s01\n",
        verify_verdict=None,
    )
    assert errs_cr == []

    rf = (
        tmp_path
        / "memory-bank"
        / "back"
        / "reflection"
        / "reflection-T-x.md"
    )
    rf.parent.mkdir(parents=True)
    rf.write_text(
        "# BACK REFLECT — T-x\n\n**Статус:** completed\n\n"
        "## Сравнение с планом\n- ok\n\n## Что сработало\n- a\n\n## Уроки\n- b\n",
        encoding="utf-8",
    )
    rel_rf = str(rf.relative_to(tmp_path))
    errs_rf = el.crosscheck_result_artifacts(
        tmp_path,
        {"status": "ok", "mode": "REFLECT", "artifact": rel_rf},
        last_mode="REFLECT",
        decompose=None,
        step_path=None,
        handoff="- **Следующий:** BACK ARCHIVE NOW\n",
        verify_verdict=None,
    )
    assert errs_rf == []

    errs_rf_bad = el.crosscheck_result_artifacts(
        tmp_path,
        {"status": "ok", "mode": "REFLECT", "artifact": rel_rf},
        last_mode="REFLECT",
        decompose=None,
        step_path=None,
        handoff="- **Следующий:** BACK IMPLEMENT\n",
        verify_verdict=None,
    )
    assert any("ARCHIVE NOW" in e for e in errs_rf_bad)


def test_crosscheck_trusts_result_not_index_status(tmp_path: Path):
    """FINISH gate = result.yaml + artifact; index.md may lag (human view)."""
    el = _load("epic_lib")
    dec = tmp_path / "memory-bank" / "back" / "plan" / "decompose-x" / "index.md"
    dec.parent.mkdir(parents=True)
    dec.write_text(
        "| Step | Title | Shard | Status |\n"
        "|------|-------|-------|--------|\n"
        "| **s01** | Foo | s01-foo.yaml | pending |\n"
        "| **s02** | Bar | s02-bar.yaml | pending |\n",
        encoding="utf-8",
    )
    step = _write_back_implement_yaml(
        tmp_path,
        "memory-bank/back/implement/implement-x/s01-foo.yaml",
        step_id="s01",
    )
    errs = el.crosscheck_ok_result(
        tmp_path,
        {
            "status": "ok",
            "mode": "IMPLEMENT",
            "step_id": "s01",
            "artifact": str(step.relative_to(tmp_path)),
        },
        last_mode="IMPLEMENT",
        decompose=str(dec.relative_to(tmp_path)),
        step_path=str(step.relative_to(tmp_path)),
        handoff="- **code_changed:** no\n- **Следующий:** BACK IMPLEMENT @s02\n",
        verify_verdict=None,
    )
    assert errs == []
    assert el.decompose_step_status(tmp_path, str(dec), "s01") == "pending"


def test_epic_remaining_is_pending_canon(tmp_path: Path):
    el = _load("epic_lib")
    # seed loop transitions for loop_engine
    loop_dir = tmp_path / "loop"
    loop_dir.mkdir(parents=True)
    root = Path(__file__).resolve().parents[2]
    loop_dir.joinpath("transitions.yaml").write_text(
        (root / "loop" / "transitions.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    dec = tmp_path / "memory-bank" / "back" / "plan" / "decompose-x" / "index.md"
    dec.parent.mkdir(parents=True)
    dec.write_text(
        "| step_id | title | needs_creative | next_phase | status |\n"
        "| :--- | :--- | :---: | :--- | :--- |\n"
        "| **s10** | reports | no | BACK IMPLEMENT | completed |\n"
        "| **s11** | vessel | yes (CR-P2-09) | BACK CREATIVE | pending |\n"
        "| **s12** | ota | yes (CR-P2-10) | BACK CREATIVE | pending |\n",
        encoding="utf-8",
    )
    rem = el.seed_epic_remaining(tmp_path, str(dec), force=True)
    assert [r["id"] for r in rem] == ["s11", "s12"]
    assert el.decompose_pending_left(tmp_path, str(dec)) == 2
    assert el.command_when_pending_left(tmp_path, str(dec), "BACK") == "BACK CREATIVE"
    el.complete_epic_remaining_step(tmp_path, "s11")
    assert el.decompose_pending_left(tmp_path, str(dec)) == 1
    # index still says s11 pending — machine queue already advanced
    assert el.decompose_step_status(tmp_path, str(dec), "s11") == "pending"


def test_decompose_step_status_ignores_needs_creative_no(tmp_path: Path):
    el = _load("epic_lib")
    dec = tmp_path / "memory-bank" / "back" / "plan" / "decompose-x" / "index.md"
    dec.parent.mkdir(parents=True)
    dec.write_text(
        "| step_id | title | implement | needs_creative | tdd | next_phase | status |\n"
        "| :--- | :--- | :--- | :---: | :---: | :--- | :--- |\n"
        "| **s10** | reports | [s10](x) | no | yes | BACK IMPLEMENT | completed |\n"
        "| **s11** | vessel | [s11](x) | yes (CR-P2-09) | yes | BACK CREATIVE | pending |\n",
        encoding="utf-8",
    )
    assert el.decompose_step_status(tmp_path, str(dec), "s10") == "completed"
    assert el.decompose_step_status(tmp_path, str(dec), "s11") == "pending"
    # no loop-state remaining yet → seed from index on pending/next
    assert el.decompose_pending_left(tmp_path, str(dec)) == 1
    assert el.command_when_pending_left(tmp_path, str(dec), "BACK") == "BACK CREATIVE"


def test_crosscheck_forbids_qa_while_pending(tmp_path: Path):
    el = _load("epic_lib")
    dec = tmp_path / "memory-bank" / "back" / "plan" / "decompose-x" / "index.md"
    dec.parent.mkdir(parents=True)
    dec.write_text(
        "| Step | Title | Shard | Status |\n"
        "|------|-------|-------|--------|\n"
        "| **s01** | Foo | s01-foo.md | completed |\n"
        "| **s02** | Bar | s02-bar.md | pending |\n",
        encoding="utf-8",
    )
    step = tmp_path / "memory-bank" / "back" / "implement" / "implement-x" / "s01-foo.md"
    step.parent.mkdir(parents=True)
    step.write_text(
        "# [T-001 | s01 | foo] IMPLEMENT\n\n"
        "**Plan ID:** x\n**Decompose step:** s01\n**Implement index:** i\n"
        "**Дата:** 2026-07-31\n**Уровень:** 2\n**Статус:** completed\n\n"
        "## Сделано\n- a\n\n## Файлы\n- f\n\n## Тесты\n- t\n\n"
        "## Integration check\n- ok\n",
        encoding="utf-8",
    )
    errs = el.crosscheck_ok_result(
        tmp_path,
        {
            "status": "ok",
            "mode": "IMPLEMENT",
            "step_id": "s01",
            "artifact": str(step.relative_to(tmp_path)),
        },
        last_mode="IMPLEMENT",
        decompose=str(dec.relative_to(tmp_path)),
        step_path=str(step.relative_to(tmp_path)),
        handoff=(
            "- **code_changed:** no\n"
            "- **Следующий:** BACK QA v1-demo\n"
        ),
        verify_verdict=None,
    )
    assert any("QA запрещён" in e and "pending=" in e for e in errs)


def test_crosscheck_decompose_completed(tmp_path: Path):
    el = _load("epic_lib")
    dec = tmp_path / "memory-bank" / "back" / "plan" / "decompose-x" / "index.md"
    dec.parent.mkdir(parents=True)
    dec.write_text(
        "| Step | Title | Shard | Status |\n"
        "|------|-------|-------|--------|\n"
        "| **s01** | Foo | s01-foo.yaml | completed |\n"
        "| **s02** | Bar | s02-bar.yaml | pending |\n",
        encoding="utf-8",
    )
    assert el.decompose_step_status(tmp_path, str(dec), "s01") == "completed"
    assert el.decompose_step_status(tmp_path, str(dec), "s02") == "pending"

    step = _write_back_implement_yaml(
        tmp_path,
        "memory-bank/back/implement/implement-x/s01-foo.yaml",
        step_id="s01",
    )
    errs = el.crosscheck_ok_result(
        tmp_path,
        {
            "status": "ok",
            "mode": "IMPLEMENT",
            "step_id": "s01",
            "artifact": str(step.relative_to(tmp_path)),
        },
        last_mode="IMPLEMENT",
        decompose=str(dec.relative_to(tmp_path)),
        step_path=str(step.relative_to(tmp_path)),
        handoff="- **code_changed:** no\n- **Следующий:** BACK IMPLEMENT @s02\n",
        verify_verdict=None,
    )
    assert errs == []

    errs_bad = el.crosscheck_ok_result(
        tmp_path,
        {
            "status": "ok",
            "mode": "IMPLEMENT",
            "artifact": str(step.relative_to(tmp_path)),
        },
        last_mode="IMPLEMENT",
        decompose=str(dec.relative_to(tmp_path)),
        step_path=str(step.relative_to(tmp_path)),
        handoff="- **code_changed:** no\n",
        verify_verdict=None,
    )
    assert any("step_id" in e for e in errs_bad)


def test_resolve_decompose_arm_by_path(tmp_path: Path):
    el = _load("epic_lib")
    for role_dir, role, track in (
        ("back", "BACK", "epic"),
        ("front", "FRONT", "epic"),
        ("integration", "INTEG", "program"),
    ):
        dec = tmp_path / "memory-bank" / role_dir / "plan" / "decompose-demo"
        dec.mkdir(parents=True)
        (dec / "index.md").write_text("# demo\n", encoding="utf-8")
        r = el.resolve_decompose_arm(tmp_path, f"decompose-demo")
        # bare id prefers back/ first — use full path for non-back
        if role_dir != "back":
            r = el.resolve_decompose_arm(
                tmp_path,
                f"memory-bank/{role_dir}/plan/decompose-demo",
            )
        assert r["role"] == role
        assert r["track"] == track
        assert r["decompose"].endswith(f"{role_dir}/plan/decompose-demo/index.md")
        if role == "INTEG":
            assert r["program_id"] == "INTEG-demo"
            assert r["integ_decompose"] == r["decompose"]


def test_resolve_decompose_arm_role_override(tmp_path: Path):
    el = _load("epic_lib")
    dec = tmp_path / "memory-bank" / "integration" / "plan" / "decompose-x"
    dec.mkdir(parents=True)
    (dec / "index.md").write_text("# x\n", encoding="utf-8")
    r = el.resolve_decompose_arm(
        tmp_path,
        "memory-bank/integration/plan/decompose-x",
        role="INTEG",
        track="epic",
    )
    assert r["role"] == "INTEG"
    assert r["track"] == "epic"


def test_arm_epic_infers_front_role(tmp_path: Path):
    el = _load("epic_lib")
    (tmp_path / "memory-bank").mkdir()
    (tmp_path / "memory-bank" / "activeContext.md").write_text("#\n", encoding="utf-8")
    dec = tmp_path / "memory-bank" / "front" / "plan" / "decompose-ui"
    dec.mkdir(parents=True)
    (dec / "index.md").write_text("# ui\n", encoding="utf-8")
    # seed minimal loop transitions for _sync_loop_ledger
    _seed_transitions(tmp_path)
    st = el.arm_epic(tmp_path, "memory-bank/front/plan/decompose-ui")
    assert st["role_prefix"] == "FRONT"
    assert "front/plan/decompose-ui/index.md" in st["decompose"]


def test_arm_new_epic_ignores_stale_back_archive_handoff(tmp_path: Path) -> None:
    el = _load("epic_lib")
    le = _load("loop_engine")
    _seed_transitions(tmp_path)
    (tmp_path / "memory-bank").mkdir(parents=True, exist_ok=True)
    (tmp_path / "memory-bank" / "activeContext.md").write_text(
        "## load_now\n"
        "- [reflection](back/reflection/reflection-T-005.md)\n\n"
        "## Handoff BACK REFLECT T-005\n"
        "- **Следующий:** BACK ARCHIVE NOW\n",
        encoding="utf-8",
    )
    le.save_loop_state(
        tmp_path,
        {
            "version": 1,
            "active": False,
            "status": "complete",
            "role": "BACK",
            "mode": "ARCHIVE",
            "journey": {"id": "BACK-v1-p2-ship", "phase": "COMPLETE"},
            "epic": {
                "decompose": "memory-bank/back/plan/decompose-v1-p2-ship/index.md",
                "plan_id": "v1-p2-ship",
                "remaining": [],
                "pending": 0,
            },
            "next": {"command": "BACK ARCHIVE NOW", "target": "T-005"},
            "step": {"id": None, "shard": None, "artifact": None},
            "queue": [],
            "resume": {"command": None, "implement": None, "gap": None},
            "verdict": "pass",
            "halt_reason": None,
            "model": None,
            "notes": None,
        },
    )
    dec = tmp_path / "memory-bank" / "integration" / "plan" / "decompose-v1-portal"
    dec.mkdir(parents=True)
    (dec / "index.md").write_text(
        "| step | title | status |\n"
        "| --- | --- | --- |\n"
        "| **e01** | home | pending |\n"
        "| **e02** | login | pending |\n",
        encoding="utf-8",
    )

    el.arm_epic(tmp_path, "decompose-v1-portal", role_prefix="INTEG")
    resolved = el.resolve_next(tmp_path)

    assert resolved["ok"] is True
    assert resolved["command"] == "INTEG IMPLEMENT"
    ls = le.load_loop_state(tmp_path)
    assert ls["epic"]["pending"] == 2
    assert ls["status"] == "running"
    assert ls["role"] == "INTEG"
    assert (ls.get("next") or {}).get("command") == "INTEG IMPLEMENT"


def test_arm_force_implement_mode(tmp_path: Path) -> None:
    el = _load("epic_lib")
    le = _load("loop_engine")
    _seed_transitions(tmp_path)
    (tmp_path / "memory-bank").mkdir(parents=True, exist_ok=True)
    (tmp_path / "memory-bank" / "activeContext.md").write_text("# ctx\n", encoding="utf-8")
    dec = tmp_path / "memory-bank" / "integration" / "plan" / "decompose-portal"
    dec.mkdir(parents=True)
    (dec / "index.md").write_text(
        "| step | title | next | status |\n"
        "| --- | --- | --- | --- |\n"
        "| **e01** | x | INTEG CREATIVE | pending |\n",
        encoding="utf-8",
    )
    el.arm_epic(
        tmp_path,
        "decompose-portal",
        role_prefix="INTEG",
        force_mode="IMPLEMENT",
    )
    ls = le.load_loop_state(tmp_path)
    assert ls["mode"] == "IMPLEMENT"
    assert (ls.get("next") or {}).get("command") == "INTEG IMPLEMENT"
