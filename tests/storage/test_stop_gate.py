from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STOP_GATE = ROOT / ".claude" / "hooks" / "stop-gate.py"
EPIC_LIB_PATH = ROOT / ".claude" / "hooks" / "epic_lib.py"
HOOKS = ROOT / ".claude" / "hooks"
if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))


def _load_epic_lib():
    spec = importlib.util.spec_from_file_location("epic_lib", EPIC_LIB_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write(rel: str, body: str, cwd: Path) -> None:
    path = cwd / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _run_stop_gate(cwd: Path, payload: dict, *, epic_loop: bool = True) -> dict:
    env = os.environ.copy()
    if epic_loop:
        env["EPIC_LOOP"] = "1"
    else:
        env.pop("EPIC_LOOP", None)
    proc = subprocess.run(
        [sys.executable, str(STOP_GATE)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    out = (proc.stdout or "").strip()
    if not out:
        return {}
    return json.loads(out)


def test_stop_gate_blocks_early_end_without_fingerprint_progress(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    _write(
        "memory-bank/back/plan/decompose-sg/index.md",
        "| Step | Status |\n| --- | --- |\n| **s01** | pending |\n",
        tmp_path,
    )
    handoff = (
        "## load_now\n"
        "- `memory-bank/back/plan/decompose-sg/index.md`\n\n"
        "## Handoff BACK CREATIVE — done\n"
        "- **Следующий:** BACK IMPLEMENT @s01\n"
    )
    _write("memory-bank/activeContext.md", handoff, tmp_path)
    epic_lib.arm_epic(tmp_path, "decompose-sg", role_prefix="BACK")
    # simulate resolve: fingerprint captured before session work
    resolved = epic_lib.resolve_next(tmp_path)
    assert resolved["ok"] is True
    assert resolved["command"] == "BACK IMPLEMENT"

    result = _run_stop_gate(
        tmp_path,
        {
            "session_id": "test-early-stop",
            "cwd": str(tmp_path),
            "last_assistant_message": "OK BACK IMPLEMENT — начинаю.\nМодель ИИ: GPT.",
            "stop_hook_active": False,
        },
    )
    assert result.get("decision") == "block"
    assert "epic-gate" in result.get("reason", "")
    assert "начинаю" in result.get("reason", "") or "Handoff" in result.get("reason", "")


def test_stop_gate_allows_after_handoff_fingerprint_change(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    _write(
        "memory-bank/back/plan/decompose-sg2/index.md",
        "| Step | Status |\n| --- | --- |\n| **s01** | pending |\n",
        tmp_path,
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/back/plan/decompose-sg2/index.md`\n\n"
        "## Handoff BACK\n- **Следующий:** BACK IMPLEMENT @s01\n",
        tmp_path,
    )
    epic_lib.arm_epic(tmp_path, "decompose-sg2", role_prefix="BACK")
    epic_lib.resolve_next(tmp_path)

    _write(
        "loop/runtime/epic/result.yaml",
        "version: 1\nstatus: ok\ndraft: false\n",
        tmp_path,
    )

    # FINISH: rewrite handoff (fingerprint changes)
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n"
        "- `memory-bank/back/plan/decompose-sg2/s01.md`\n\n"
        "## Handoff BACK IMPLEMENT s01 — done\n"
        "- **Следующий:** BACK IMPLEMENT @s02\n",
        tmp_path,
    )

    result = _run_stop_gate(
        tmp_path,
        {
            "session_id": "test-finish-ok",
            "cwd": str(tmp_path),
            "last_assistant_message": "FINISH: Handoff updated.",
            "stop_hook_active": False,
        },
    )
    assert result == {}


def test_stop_gate_blocks_invalid_result_status_pass(tmp_path: Path) -> None:
    """status:pass alone without mode/verdict — after normalize may still need QA fields;
    pending stub must block on first stop."""
    epic_lib = _load_epic_lib()
    _write(
        "memory-bank/back/plan/decompose-sg-pass/index.md",
        "| Step | Status |\n| --- | --- |\n| **s01** | pending |\n",
        tmp_path,
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n- `memory-bank/back/plan/decompose-sg-pass/index.md`\n\n"
        "## Handoff BACK QA — done\n- **Следующий:** BACK REFLECT\n",
        tmp_path,
    )
    epic_lib.arm_epic(tmp_path, "decompose-sg-pass", role_prefix="BACK")
    # force last_command QA via state
    st = epic_lib.load_epic_state(tmp_path)
    st["last_command"] = "BACK QA"
    epic_lib.save_epic_state(tmp_path, st)
    epic_lib.resolve_next(tmp_path)

    _write(
        "loop/runtime/epic/result.yaml",
        "version: 1\nstatus: pending\ndraft: true\nmode: QA\n",
        tmp_path,
    )
    _write(
        "memory-bank/activeContext.md",
        "## load_now\n"
        "- `memory-bank/back/qa/v1/qa-x.md`\n\n"
        "## Handoff BACK QA — pass\n"
        "- **Следующий:** BACK REFLECT\n",
        tmp_path,
    )

    blocked = _run_stop_gate(
        tmp_path,
        {
            "session_id": "test-qa-bad-result",
            "cwd": str(tmp_path),
            "last_assistant_message": "BACK QA — PASS. FINISH.",
            "stop_hook_active": False,
        },
    )
    assert blocked.get("decision") == "block"
    assert "result.yaml" in blocked.get("reason", "")

    # status:pass + mode QA + verdict pass → normalize makes valid → allow stop
    _write(
        "loop/runtime/epic/result.yaml",
        "version: 1\nstatus: pass\nmode: QA\nverdict: pass\ndraft: false\n",
        tmp_path,
    )
    allowed = _run_stop_gate(
        tmp_path,
        {
            "session_id": "test-qa-pass-alias",
            "cwd": str(tmp_path),
            "last_assistant_message": "BACK QA — PASS. FINISH.",
            "stop_hook_active": False,
        },
    )
    assert allowed == {}
    # file rewritten to status: ok
    text = (tmp_path / "loop/runtime/epic/result.yaml").read_text(encoding="utf-8")
    assert "status: ok" in text
    assert "status: pass" not in text


def test_stop_gate_inactive_outside_epic_loop(tmp_path: Path) -> None:
    _write(
        "memory-bank/activeContext.md",
        "## Handoff BACK\n- hello\n",
        tmp_path,
    )
    result = _run_stop_gate(
        tmp_path,
        {
            "session_id": "test-no-epic",
            "cwd": str(tmp_path),
            "last_assistant_message": "OK начинаю",
            "stop_hook_active": False,
        },
        epic_loop=False,
    )
    assert result == {}
