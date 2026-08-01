#!/usr/bin/env python3
"""Stop — block parent stop without mandatory verify/reviewer when finishing."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import FINISH_RE, load_state, read_stdin, save_state  # noqa: E402
from epic_lib import (  # noqa: E402
    extract_handoff_block,
    halt_epic,
    load_epic_state,
    read_active_context,
)
import os


def main() -> None:
    data = read_stdin()
    session_id = data.get("session_id") or ""
    cwd = data.get("cwd") or ""
    msg = data.get("last_assistant_message") or ""
    st = load_state(session_id, cwd)
    epic = load_epic_state(cwd) if cwd else {}
    epic_loop = str(os.environ.get("EPIC_LOOP", "")).lower() in {"1", "true", "yes"}
    epic_on = bool(
        epic_loop and epic.get("active") and epic.get("status") == "running"
    )
    stop_hook_active = bool(data.get("stop_hook_active"))

    # Default anti-loop: allow stop after a prior hook block — EXCEPT epic (need FINISH).
    if stop_hook_active and not epic_on:
        return

    finishing = bool(FINISH_RE.search(msg))
    # also treat explicit "done" after suite language
    if not finishing and st.get("mode") == "qa":
        finishing = bool(
            re.search(
                r"(?i)(suite\s+(green|pass)|qa\s+pass|FINISH\s+QA|блокеры зафиксир)",
                msg,
            )
        )

    if st.get("need_verify") and finishing and not st.get("verify_done"):
        if stop_hook_active:
            return
        payload = {
            "decision": "block",
            "reason": (
                "spawn-gate: перед FINISH/Handoff обязателен @verify "
                "(Agent subagent_type=verify) с packed AC+ · AC− · §0.11 · VERIFY · ALLOW READ. "
                "После VERDICT: PASS можно остановиться. "
                f"state={json.dumps({k: st.get(k) for k in ('mode','need_verify','verify_done','verify_verdict')})}"
            ),
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        return

    if st.get("need_reviewer") and finishing and not st.get("reviewer_done"):
        if stop_hook_active:
            return
        payload = {
            "decision": "block",
            "reason": (
                "spawn-gate: BACK QA FINISH без @reviewer запрещён. "
                "Сначала Agent subagent_type=reviewer с Suite results · AC+ · AC− · §0.11 · ALLOW READ. "
                f"state={json.dumps({k: st.get(k) for k in ('mode','need_reviewer','reviewer_done','reviewer_verdict')})}"
            ),
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        return

    if st.get("mode") == "qa" and finishing and st.get("reviewer_done"):
        ac = Path(cwd) / "memory-bank" / "activeContext.md" if cwd else None
        handoff_ok = False
        if ac and ac.is_file():
            text = ac.read_text(encoding="utf-8", errors="replace")
            handoff_ok = bool(
                re.search(r"(?im)^##\s*Handoff\s+.*\bQA\b", text)
            ) or bool(re.search(r"(?im)^##\s*Handoff\s+BACK QA\b", text))
        if not handoff_ok:
            if stop_hook_active:
                return
            payload = {
                "decision": "block",
                "reason": (
                    "spawn-gate: BACK QA FINISH без Handoff QA в memory-bank/activeContext.md. "
                    "Перепиши ## Handoff BACK QA … (pass→next; blocked→BUGFIX) + load_now, "
                    "затем остановись."
                ),
            }
            sys.stdout.write(json.dumps(payload, ensure_ascii=False))
            return

    if st.get("verify_done") and st.get("verify_verdict") == "FAIL" and finishing:
        if stop_hook_active:
            return
        payload = {
            "decision": "block",
            "reason": (
                "spawn-gate: verify=FAIL — нельзя FINISH. Исправь blockers, "
                "снова @verify до VERDICT: PASS."
            ),
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        return

    if epic_on and finishing:
        handoff = extract_handoff_block(read_active_context(cwd))
        if not handoff:
            blocks = int(st.get("epic_stop_blocks") or 0) + 1
            st["epic_stop_blocks"] = blocks
            save_state(session_id, cwd, st)
            if blocks >= 3:
                halt_epic(cwd, "FINISH claimed but no Handoff (stop×3)")
                return
            payload = {
                "decision": "block",
                "reason": (
                    "epic-gate: FINISH без ## Handoff в memory-bank/activeContext.md. "
                    "Запиши Handoff + load_now (следующая команда), затем stop — "
                    f"epic-loop поднимет НОВУЮ сессию. Попытка {blocks}/3."
                ),
            }
            sys.stdout.write(json.dumps(payload, ensure_ascii=False))
            return
        st["epic_stop_blocks"] = 0
        save_state(session_id, cwd, st)
        return

    if epic_on and not finishing:
        blocks = int(st.get("epic_stop_blocks") or 0) + 1
        st["epic_stop_blocks"] = blocks
        save_state(session_id, cwd, st)
        if blocks >= 3:
            halt_epic(cwd, "stuck without FINISH (stop×3)")
            return
        payload = {
            "decision": "block",
            "reason": (
                "epic-gate: нельзя остановиться без FINISH. "
                "Сделай step + ## Handoff в activeContext (Следующий: BACK IMPLEMENT|CREATIVE|QA|…) "
                f"и stop. Попытка {blocks}/3; дальше epic halt. "
                "Или: python3 .claude/hooks/epic_resolve.py halt --reason '…'"
            ),
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        return


if __name__ == "__main__":
    main()
