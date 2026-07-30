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
