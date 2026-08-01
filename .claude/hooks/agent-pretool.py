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
                    else "AC+ / AC− / §0.11 / VERIFY / RESULT / ALLOW READ"
                )
            )
        for v in allow_read_violations(prompt):
            deny_reasons.append(v)

    if norm == "verify":
        if st.get("verify_done") and str(st.get("verify_verdict") or "").upper() == "PASS":
            deny_reasons.append(
                "verify_already_pass: VERDICT: PASS уже есть — не повторять @verify; "
                "пиши FINISH (Handoff/step) и stop. "
                "Retry @verify разрешён только после FAIL или spawn DENY."
            )
        elif cwd:
            try:
                from session_result import (
                    is_finalized_result,
                    load_and_normalize_result,
                    result_path,
                )

                res, _norm_changes = load_and_normalize_result(
                    cwd, track="epic", persist=True
                )
                if res is None:
                    deny_reasons.append(
                        f"result_missing: нет {result_path(cwd, 'epic')} — "
                        "сначала Write implement step → finalize result.yaml "
                        "(status≠pending, draft=false), потом @verify"
                    )
                elif not is_finalized_result(res):
                    deny_reasons.append(
                        "result_not_final: result.yaml ещё stub "
                        f"(status={res.get('status')!r} draft={res.get('draft')!r}) — "
                        "Write implement step (если нет) → finalize до spawn verify; "
                        "verify только читает"
                    )
            except Exception as exc:
                deny_reasons.append(f"result_check_error: {exc}")

    if deny_reasons:
        reason = f"spawn-gate [{norm}]: " + " | ".join(deny_reasons)
        emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                    "additionalContext": (
                        f"spawn-gate DENY [{norm}]: subagent НЕ запущен. "
                        f"{reason} "
                        "Исправь prompt/blockers → retry @"
                        f"{norm} (не FINISH)."
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
