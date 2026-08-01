#!/usr/bin/env python3
"""UserPromptSubmit — set spawn-gate mode + inject spawn map."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    FINISH_RE,
    IMPL_RE,
    QA_RE,
    SPAWN_MAP,
    emit,
    load_state,
    read_stdin,
    save_state,
)


def main() -> None:
    data = read_stdin()
    prompt = data.get("prompt") or data.get("user_prompt") or ""
    session_id = data.get("session_id") or ""
    cwd = data.get("cwd") or ""
    st = load_state(session_id, cwd)

    ctx_parts = [SPAWN_MAP]

    if QA_RE.search(prompt):
        st["mode"] = "qa"
        st["need_reviewer"] = True
        st["reviewer_done"] = False
        st["reviewer_verdict"] = None
        ctx_parts.append(
            "MODE=BACK QA → после полного planned suite (storage + not slow / live по scope) "
            "обязательно 1× Agent/subagent_type=reviewer с секциями-заголовками: "
            "Suite results · AC+ · AC− · §0.11 · ALLOW READ (≤10 файлов, не деревья). "
            "FORBIDDEN: isolation=worktree; model= override; 2× reviewer без новой причины. "
            "Без reviewer FINISH QA = FAIL. FINISH → переписать Handoff в activeContext "
            "(pass→next; blocked→BUGFIX)."
        )
    elif IMPL_RE.search(prompt) or "BACK IMPLEMENT" in prompt.upper():
        st["mode"] = "implement"
        st["need_verify"] = True
        # новый IMPLEMENT-чат — сброс verify gate
        if not FINISH_RE.search(prompt):
            st["verify_done"] = False
            st["verify_verdict"] = None
        ctx_parts.append(
            "MODE=IMPLEMENT → делегируй через Agent как обычно (built-in или @explorer). "
            "Порядок: Write implement step на диск → Handoff → finalize result.yaml "
            "(artifact=implement path, не decompose) → Agent/subagent_type=verify "
            "(AC+ · AC− · §0.11 · VERIFY · RESULT · ALLOW) → FINISH. "
            "VERDICT: FAIL или spawn DENY → чини blockers/prompt → снова @verify. "
            "FORBIDDEN: @verify после VERDICT: PASS; finalize/@verify до step-файла. "
            "Overlay: @explorer (поиск) · @verify · @reviewer."
        )

    if FINISH_RE.search(prompt) and st.get("mode") == "implement":
        st["need_verify"] = True
        if st.get("verify_done") and st.get("verify_verdict") == "PASS":
            ctx_parts.append(
                "FINISH detected → @verify уже PASS — не повторять; допиши Handoff/step и stop."
            )
        else:
            ctx_parts.append(
                "FINISH detected → если нет PASS: Write step (если нет) → "
                "finalize result → @verify; "
                "при FAIL/DENY — fix → снова @verify до PASS → stop. "
                "Stop-hook заблокирует стоп без VERDICT: PASS."
            )
    if FINISH_RE.search(prompt) and st.get("mode") == "qa":
        st["need_reviewer"] = True
        ctx_parts.append(
            "QA FINISH detected → @reviewer VERDICT уже нужен; "
            "обязателен Handoff в activeContext.md (не только qa-*.yaml / tasks.md). "
            "Stop-hook заблокирует стоп без VERDICT reviewer."
        )

    save_state(session_id, cwd, st)
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n".join(ctx_parts),
            }
        }
    )


if __name__ == "__main__":
    main()
