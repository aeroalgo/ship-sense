#!/usr/bin/env python3
"""SubagentStop — require VERDICT for verify/reviewer; mark gates done."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    extract_verdict,
    load_state,
    normalize_type,
    read_stdin,
    save_state,
)


def main() -> None:
    data = read_stdin()
    if data.get("stop_hook_active"):
        return

    agent_type = normalize_type(data.get("agent_type")) or data.get("agent_type")
    msg = data.get("last_assistant_message") or ""
    session_id = data.get("session_id") or ""
    cwd = data.get("cwd") or ""
    st = load_state(session_id, cwd)
    verdict = extract_verdict(msg)

    if agent_type in {"verify", "reviewer"} and not verdict:
        print(
            f"{agent_type}: в финале обязателен VERDICT: PASS|FAIL"
            + ("|BLOCKED" if agent_type == "reviewer" else "")
            + ". Допиши отчёт в формате агента, затем остановись.",
            file=sys.stderr,
        )
        sys.exit(2)

    if agent_type == "verify" and verdict:
        st["verify_done"] = True
        st["verify_verdict"] = verdict
        save_state(session_id, cwd, st)
        if verdict == "FAIL":
            print(
                "verify VERDICT: FAIL — parent чинит только blockers, "
                "потом снова @verify. Не FINISH.",
                file=sys.stderr,
            )
            # don't block stop of subagent on FAIL — parent must see result
            return

    if agent_type == "reviewer" and verdict:
        st["reviewer_done"] = True
        st["reviewer_verdict"] = verdict
        save_state(session_id, cwd, st)


if __name__ == "__main__":
    main()
