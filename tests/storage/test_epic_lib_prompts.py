from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EPIC_LIB_PATH = ROOT / ".claude" / "hooks" / "epic_lib.py"


def _load_epic_lib():
    spec = importlib.util.spec_from_file_location("epic_lib", EPIC_LIB_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write(rel_path: str, body: str, cwd: Path) -> str:
    path = cwd / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return rel_path


def test_build_prompt_implement_packs_verify_contract(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    step = _write(
        "memory-bank/back/plan/decompose-demo/s01-demo.md",
        "# s01\n\n- `.venv/bin/pytest tests/storage/test_demo.py -q`\n",
        tmp_path,
    )
    qa = _write("memory-bank/back/qa/qa-demo.md", "# qa\n", tmp_path)

    prompt = epic_lib.build_prompt("BACK IMPLEMENT", tmp_path, [qa, step])

    assert "## spawn-gate IMPLEMENT" in prompt
    assert "\nAC+:\n" in prompt
    assert "\nAC−:\n" in prompt
    assert "\n§0.11:\n" in prompt
    assert "\nVERIFY:\n" in prompt
    assert ".venv/bin/pytest tests/storage/test_demo.py -q" in prompt
    assert "ALLOW READ: memory-bank/back/qa/qa-demo.md, memory-bank/back/plan/decompose-demo/s01-demo.md" in prompt


def test_build_prompt_refactor_packs_verify_contract(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    step = _write(
        "memory-bank/back/refactor/plan/decompose-demo/r01-demo.md",
        "# r01\n\n- `.venv/bin/pytest tests/storage/test_refactor.py -q`\n",
        tmp_path,
    )

    prompt = epic_lib.build_prompt("BACK REFACTOR", tmp_path, [step])

    assert "## spawn-gate REFACTOR" in prompt
    assert "behavior freeze" in prompt.lower() or "Behavior freeze" in prompt
    assert "\nAC+:\n" in prompt
    assert "\nAC−:\n" in prompt
    assert "\n§0.11:\n" in prompt
    assert "\nVERIFY:\n" in prompt
    assert ".venv/bin/pytest tests/storage/test_refactor.py -q" in prompt
    assert "ALLOW READ: memory-bank/back/refactor/plan/decompose-demo/r01-demo.md" in prompt


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
    assert "## spawn-gate REFACTOR" in (resolved["prompt"] or "")


def test_build_prompt_bugfix_packs_verify_contract(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    bugfix = _write(
        "memory-bank/back/bugfix/bugfix-demo.md",
        "# bugfix\n\n- `.venv/bin/pytest tests/storage/test_bugfix.py -q`\n",
        tmp_path,
    )

    prompt = epic_lib.build_prompt("BACK BUGFIX", tmp_path, [bugfix])

    assert "## spawn-gate BUGFIX" in prompt
    assert "\nAC+:\n" in prompt
    assert "\nAC−:\n" in prompt
    assert "\n§0.11:\n" in prompt
    assert "\nVERIFY:\n" in prompt
    assert ".venv/bin/pytest tests/storage/test_bugfix.py -q" in prompt
    assert "ALLOW READ: memory-bank/back/bugfix/bugfix-demo.md" in prompt


def test_build_prompt_qa_packs_reviewer_contract(tmp_path: Path) -> None:
    epic_lib = _load_epic_lib()
    qa = _write("memory-bank/back/qa/qa-demo.md", "# qa\n", tmp_path)
    step = _write("memory-bank/back/implement/implement-demo/s01-demo.md", "# impl\n", tmp_path)

    prompt = epic_lib.build_prompt("BACK QA", tmp_path, [qa, step])

    assert "## spawn-gate BACK QA" in prompt
    assert "\nSuite results:\n" in prompt
    assert "\nAC+:\n" in prompt
    assert "\nAC−:\n" in prompt
    assert "\n§0.11:\n" in prompt
    assert "ALLOW READ: memory-bank/back/qa/qa-demo.md, memory-bank/back/implement/implement-demo/s01-demo.md" in prompt
    assert ".cursor/rules/**" not in prompt.split("ALLOW READ:", 1)[1].splitlines()[0]
