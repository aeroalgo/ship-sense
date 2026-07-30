#!/usr/bin/env python3
"""PreToolUse Agent — normalize type, contract gate, strip worktree/model, HARD RULE."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    ALLOWED,
    GATE_AGENTS,
    HARD_RULE,
    allow_read_violations,
    emit,
    load_state,
    missing_contract_sections,
    normalize_agent_tool_input,
    normalize_type,
    read_stdin,
    save_state,
)


def main() -> None:
    data = read_stdin()
    if data.get("tool_name") not in {"Agent", "Task"}:
        return

    tool_input = dict(data.get("tool_input") or {})
    raw_type = tool_input.get("subagent_type") or tool_input.get("agent_type")
    norm = normalize_type(raw_type)
    session_id = data.get("session_id") or ""
    cwd = data.get("cwd") or ""
    st = load_state(session_id, cwd)

    if norm and norm != raw_type:
        tool_input["subagent_type"] = norm

    prompt = tool_input.get("prompt") or ""
    if HARD_RULE not in prompt:
        prompt = (prompt.rstrip() + "\n\n" + HARD_RULE).lstrip()
        tool_input["prompt"] = prompt

    notes = normalize_agent_tool_input(tool_input, norm)
    prompt = tool_input.get("prompt") or prompt

    deny_reasons: list[str] = []
    if norm in GATE_AGENTS:
        missing = missing_contract_sections(norm, prompt)
        if missing:
            deny_reasons.append(
                f"prompt_incomplete: нет секций [{', '.join(missing)}]. "
                "Добавь заголовки с новой строки: "
                + (
                    "Suite results / AC+ / AC− / §0.11 / ALLOW READ"
                    if norm == "reviewer"
                    else "AC+ / AC− / §0.11 / VERIFY / ALLOW READ"
                )
            )
        for v in allow_read_violations(prompt):
            deny_reasons.append(v)

    if deny_reasons:
        emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"spawn-gate [{norm}]: " + " | ".join(deny_reasons)
                    ),
                }
            }
        )
        return

    if norm in ALLOWED:
        spawns = st.setdefault("spawns", [])
        spawns.append(norm)
        st["spawns"] = spawns[-30:]
        if norm == "verify":
            st["need_verify"] = True
        if norm == "reviewer":
            st["need_reviewer"] = True
        save_state(session_id, cwd, st)

    ctx = (
        f"spawn-gate: launching {tool_input.get('subagent_type') or raw_type}. "
        "CC делегирует как обычно; gate’ы verify/reviewer — packed prompt."
    )
    if notes:
        ctx += " Adjusted: " + "; ".join(notes) + "."

    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": tool_input,
                "additionalContext": ctx,
            }
        }
    )


if __name__ == "__main__":
    main()
