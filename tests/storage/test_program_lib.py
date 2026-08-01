from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROGRAM_LIB_PATH = ROOT / ".claude" / "hooks" / "program_lib.py"


def _load_program_lib():
    # program_lib imports epic_lib from same dir
    hooks = str(PROGRAM_LIB_PATH.parent)
    import sys

    if hooks not in sys.path:
        sys.path.insert(0, hooks)
    spec = importlib.util.spec_from_file_location("program_lib", PROGRAM_LIB_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write(rel_path: str, body: str, cwd: Path) -> str:
    path = cwd / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return rel_path


def test_parse_gap_queue_orders_back_before_front():
    pl = _load_program_lib()
    text = """
| Gap ID | x | Plan | Status |
| G-BF01 | front missing | plan-FRONT-GAP-a | open |
→ [plan-FRONT-GAP-a](../../front/plan/plan-FRONT-GAP-a.md)

| Gap ID | x | Plan | Status |
| G-FB01 | back missing | plan-BACK-GAP-b | open |
→ [plan-BACK-GAP-b](../../back/plan/plan-BACK-GAP-b.md)
"""
    q = pl.parse_gap_queue(text)
    assert [i["id"] for i in q] == ["G-FB01", "G-BF01"]
    assert q[0]["role"] == "BACK"
    assert q[1]["role"] == "FRONT"
    assert q[1]["after"] == ["G-FB01"]
    assert "plan-BACK-GAP-b.md" in (q[0]["plan"] or "")
    assert "plan-FRONT-GAP-a.md" in (q[1]["plan"] or "")


def test_next_queue_item_respects_after(tmp_path: Path):
    pl = _load_program_lib()
    queue = [
        {
            "id": "G-FB01",
            "role": "BACK",
            "status": "pending",
            "needs": ["PLAN", "DECOMPOSE", "EPIC"],
            "plan": "memory-bank/back/plan/plan-BACK-GAP-b.md",
            "decompose": None,
            "after": [],
        },
        {
            "id": "G-BF01",
            "role": "FRONT",
            "status": "pending",
            "needs": ["PLAN", "DECOMPOSE", "EPIC"],
            "plan": "memory-bank/front/plan/plan-FRONT-GAP-a.md",
            "decompose": None,
            "after": ["G-FB01"],
        },
    ]
    assert pl.next_queue_item(queue)["id"] == "G-FB01"
    queue[0]["status"] = "done"
    assert pl.next_queue_item(queue)["id"] == "G-BF01"


def test_arm_gap_fanout_resolve_plan(tmp_path: Path):
    pl = _load_program_lib()
    gap = _write(
        "memory-bank/integration/gap/gap-demo.md",
        "| G-FB01 | x | plan-BACK-GAP-x | open |\n"
        "→ [plan-BACK-GAP-x](../../back/plan/plan-BACK-GAP-x.md)\n",
        tmp_path,
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/integration/gap/gap-demo.md`\n\n"
        "## Handoff INTEG GAP\n- **Следующий:** BACK PLAN\n"
        "- **Program:** GAP_FANOUT\n"
        "- **Gap:** `memory-bank/integration/gap/gap-demo.md`\n"
        "- **Resume:** INTEG GAP CLOSE @memory-bank/integration/implement/implement-demo/e03.md\n",
        tmp_path,
    )
    pl.arm_program(
        tmp_path,
        program_id="INTEG-JOURNEY-demo",
        phase="GAP_FANOUT",
        gap_path=gap,
        resume={
            "command": "INTEG GAP CLOSE",
            "implement": "memory-bank/integration/implement/implement-demo/e03.md",
        },
    )
    r = pl.resolve_next(tmp_path)
    assert r["ok"] is True
    action = r["action"]
    assert action["kind"] == "mode"
    assert action["command"] == "BACK PLAN"
    assert action["gap_id"] == "G-FB01"
    assert "PROGRAM JOURNEY ACTIVE" in (r["prompt"] or "")


def test_fanout_after_plan_then_decompose(tmp_path: Path):
    pl = _load_program_lib()
    gap = _write(
        "memory-bank/integration/gap/gap-demo2.md",
        "| G-FB01 | x | plan-BACK-GAP-x | open |\n"
        "→ [p](../../back/plan/plan-BACK-GAP-x.md)\n",
        tmp_path,
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/back/plan/plan-BACK-GAP-x.md`\n\n"
        "## Handoff BACK PLAN\n- **Следующий:** BACK DECOMPOSE\n"
        "- **Program:** GAP_FANOUT\n",
        tmp_path,
    )
    pl.arm_program(
        tmp_path,
        program_id="demo2",
        phase="GAP_FANOUT",
        gap_path=gap,
    )
    r1 = pl.resolve_next(tmp_path)
    assert r1["action"]["command"] == "BACK PLAN"

    # simulate FINISH: fingerprint change + after
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/back/plan/plan-BACK-GAP-x.md`\n\n"
        "## Handoff BACK PLAN — done\n- **Следующий:** BACK DECOMPOSE\n"
        "- **Program:** GAP_FANOUT\n",
        tmp_path,
    )
    after = pl.after_session(tmp_path)
    assert after["ok"] is True
    assert after["phase"] == "GAP_FANOUT"

    r2 = pl.resolve_next(tmp_path)
    assert r2["action"]["command"] == "BACK DECOMPOSE"
    assert r2["action"]["gap_id"] == "G-FB01"


def test_join_to_gap_close(tmp_path: Path):
    pl = _load_program_lib()
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/integration/gap/gap-x.md`\n\n"
        "## Handoff\n- **Следующий:** INTEG GAP CLOSE\n",
        tmp_path,
    )
    st = pl.arm_program(
        tmp_path,
        program_id="join",
        phase="GAP_FANOUT",
        resume={
            "command": "INTEG GAP CLOSE",
            "implement": "memory-bank/integration/implement/implement-x/e01.md",
        },
    )
    st["queue"] = [
        {
            "id": "G-FB01",
            "role": "BACK",
            "status": "done",
            "needs": ["PLAN", "DECOMPOSE", "EPIC"],
            "plan": None,
            "decompose": None,
            "after": [],
        }
    ]
    st["phase"] = "GAP_JOIN"
    pl.save_program_state(tmp_path, st)

    r = pl.resolve_next(tmp_path)
    assert r["ok"] is True
    assert r["action"]["command"] == "INTEG GAP CLOSE"
    assert r["phase"] == "GAP_CLOSE"


def test_integ_steps_epic_action(tmp_path: Path):
    pl = _load_program_lib()
    dec = _write(
        "memory-bank/integration/plan/decompose-demo/index.md",
        "| Step | Status |\n| --- | --- |\n| **e01** | pending |\n",
        tmp_path,
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/integration/plan/decompose-demo/index.md`\n\n"
        "## Handoff INTEG\n- **Следующий:** INTEG IMPLEMENT\n",
        tmp_path,
    )
    pl.arm_program(
        tmp_path,
        program_id="steps",
        phase="INTEG_STEPS",
        integ_decompose="decompose-demo",
    )
    r = pl.resolve_next(tmp_path)
    assert r["ok"] is True
    assert r["action"]["kind"] == "epic"
    assert r["action"]["role"] == "INTEG"
    assert "decompose-demo" in (r["action"]["decompose"] or "")


def test_after_integ_epic_to_gap_open(tmp_path: Path):
    pl = _load_program_lib()
    _write(
        "memory-bank/integration/plan/decompose-demo/index.md",
        "| Step | Status |\n| --- | --- |\n| **e01** | pending |\n| **e02** | pending |\n",
        tmp_path,
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/integration/plan/decompose-demo/index.md`\n\n"
        "## Handoff INTEG\n- **Следующий:** INTEG IMPLEMENT\n",
        tmp_path,
    )
    pl.arm_program(
        tmp_path,
        program_id="to-gap",
        phase="INTEG_STEPS",
        integ_decompose="decompose-demo",
    )
    r = pl.resolve_next(tmp_path)
    assert r["action"]["kind"] == "epic"

    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/integration/implement/implement-demo/e01.md`\n\n"
        "## Handoff INTEG IMPLEMENT e01\n"
        "- **Следующий:** INTEG GAP\n"
        "- **Resume:** INTEG GAP CLOSE @memory-bank/integration/implement/implement-demo/e01.md\n",
        tmp_path,
    )
    after = pl.after_session(tmp_path, epic_status="complete")
    assert after["ok"] is True
    assert after["phase"] == "GAP_OPEN"


def test_gap_fanout_golden_path_back_then_front_to_close(tmp_path: Path):
    """End-to-end GAP_FANOUT: BACK PLAN→DECOMPOSE→epic done → FRONT → JOIN → GAP CLOSE."""
    pl = _load_program_lib()
    gap = _write(
        "memory-bank/integration/gap/gap-golden.md",
        "| Gap ID | x | Plan | Status |\n"
        "| G-FB01 | back missing | plan-BACK-GAP-g | open |\n"
        "→ [plan-BACK-GAP-g](../../back/plan/plan-BACK-GAP-g.md)\n\n"
        "| Gap ID | x | Plan | Status |\n"
        "| G-BF01 | front missing | plan-FRONT-GAP-g | open |\n"
        "→ [plan-FRONT-GAP-g](../../front/plan/plan-FRONT-GAP-g.md)\n",
        tmp_path,
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/integration/gap/gap-golden.md`\n\n"
        "## Handoff INTEG GAP\n- **Следующий:** BACK PLAN\n"
        "- **Program:** GAP_FANOUT\n"
        "- **Gap:** `memory-bank/integration/gap/gap-golden.md`\n"
        "- **Resume:** INTEG GAP CLOSE @memory-bank/integration/implement/implement-demo/e03.yaml\n",
        tmp_path,
    )
    pl.arm_program(
        tmp_path,
        program_id="INTEG-JOURNEY-golden",
        phase="GAP_FANOUT",
        gap_path=gap,
        resume={
            "command": "INTEG GAP CLOSE",
            "implement": "memory-bank/integration/implement/implement-demo/e03.yaml",
        },
    )

    r = pl.resolve_next(tmp_path)
    assert r["ok"] is True
    assert r["action"]["command"] == "BACK PLAN"
    assert r["action"]["gap_id"] == "G-FB01"

    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/back/plan/plan-BACK-GAP-g.md`\n\n"
        "## Handoff BACK PLAN\n- **Следующий:** BACK DECOMPOSE\n"
        "- **Program:** GAP_FANOUT\n",
        tmp_path,
    )
    assert pl.after_session(tmp_path)["ok"] is True

    r = pl.resolve_next(tmp_path)
    assert r["action"]["command"] == "BACK DECOMPOSE"
    assert r["action"]["gap_id"] == "G-FB01"

    _write(
        "memory-bank/activeContext.md",
        "## load_now\n"
        "- `memory-bank/back/plan/decompose-BACK-GAP-g/index.md`\n\n"
        "## Handoff BACK DECOMPOSE\n- **Следующий:** BACK IMPLEMENT\n"
        "- **Program:** GAP_FANOUT\n",
        tmp_path,
    )
    _write(
        "memory-bank/back/plan/decompose-BACK-GAP-g/index.md",
        "| Step | Status |\n| --- | --- |\n| **s01** | pending |\n",
        tmp_path,
    )
    assert pl.after_session(tmp_path)["ok"] is True

    r = pl.resolve_next(tmp_path)
    assert r["action"]["kind"] == "epic"
    assert r["action"]["role"] == "BACK"
    assert r["action"]["gap_id"] == "G-FB01"

    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/back/implement/implement-BACK-GAP-g/s01.yaml`\n\n"
        "## Handoff BACK IMPLEMENT\n- **Следующий:** BACK QA\n"
        "- **Program:** GAP_FANOUT\n",
        tmp_path,
    )
    after = pl.after_session(tmp_path, epic_status="complete")
    assert after["ok"] is True
    assert after["phase"] == "GAP_FANOUT"

    r = pl.resolve_next(tmp_path)
    assert r["ok"] is True
    assert r["action"]["command"] == "FRONT PLAN"
    assert r["action"]["gap_id"] == "G-BF01"

    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/front/plan/plan-FRONT-GAP-g.md`\n\n"
        "## Handoff FRONT PLAN\n- **Следующий:** FRONT DECOMPOSE\n"
        "- **Program:** GAP_FANOUT\n",
        tmp_path,
    )
    assert pl.after_session(tmp_path)["ok"] is True
    r = pl.resolve_next(tmp_path)
    assert r["action"]["command"] == "FRONT DECOMPOSE"

    _write(
        "memory-bank/activeContext.md",
        "## load_now\n"
        "- `memory-bank/front/plan/decompose-FRONT-GAP-g/index.md`\n\n"
        "## Handoff FRONT DECOMPOSE\n- **Следующий:** FRONT IMPLEMENT\n"
        "- **Program:** GAP_FANOUT\n",
        tmp_path,
    )
    _write(
        "memory-bank/front/plan/decompose-FRONT-GAP-g/index.md",
        "| Step | Status |\n| --- | --- |\n| **s01** | pending |\n",
        tmp_path,
    )
    assert pl.after_session(tmp_path)["ok"] is True
    r = pl.resolve_next(tmp_path)
    assert r["action"]["kind"] == "epic"
    assert r["action"]["role"] == "FRONT"

    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/front/implement/implement-FRONT-GAP-g/s01.yaml`\n\n"
        "## Handoff FRONT IMPLEMENT\n- **Следующий:** FRONT QA\n"
        "- **Program:** GAP_FANOUT\n",
        tmp_path,
    )
    after = pl.after_session(tmp_path, epic_status="complete")
    assert after["ok"] is True
    assert after["phase"] in {"GAP_JOIN", "GAP_CLOSE"}

    r = pl.resolve_next(tmp_path)
    assert r["ok"] is True
    assert r["action"]["command"] == "INTEG GAP CLOSE"
    assert r["phase"] == "GAP_CLOSE"


def test_build_prompt_front_qa_uses_role():
    import sys

    hooks = str(ROOT / ".claude" / "hooks")
    if hooks not in sys.path:
        sys.path.insert(0, hooks)
    import epic_lib

    prompt = epic_lib.build_prompt("FRONT QA", Path("/tmp"), [])
    assert "## FRONT QA (HARD)" in prompt
    assert "@reviewer" in prompt
    assert "spawn-hard.md" in prompt
    assert "## spawn-gate FRONT QA" not in prompt
