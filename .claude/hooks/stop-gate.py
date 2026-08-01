#!/usr/bin/env python3
"""Stop — block parent stop without mandatory verify/reviewer / epic FINISH."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import FINISH_RE, load_state, read_stdin, save_state  # noqa: E402
from epic_lib import (  # noqa: E402
    extract_handoff_block,
    fingerprint_context,
    halt_epic,
    load_epic_state,
    read_active_context,
    validate_active_context_shape,
)


def _block(reason: str) -> None:
    sys.stdout.write(
        json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False)
    )


def _epic_progressed(cwd: str, epic: dict) -> tuple[bool, str]:
    """True when Handoff+load_now fingerprint changed vs pending_fingerprint_before."""
    ctx = read_active_context(cwd)
    handoff = extract_handoff_block(ctx)
    before = epic.get("pending_fingerprint_before")
    now_fp = fingerprint_context(ctx)
    if not handoff.strip():
        return False, now_fp
    if before is None:
        return True, now_fp
    return now_fp != before, now_fp


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

    # Default anti-loop: allow stop after a prior hook block — EXCEPT epic (need progress).
    if stop_hook_active and not epic_on:
        return

    finishing = bool(FINISH_RE.search(msg))
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
        _block(
            "spawn-gate: перед FINISH/Handoff обязателен @verify "
            "(Agent subagent_type=verify) с packed AC+ · AC− · §0.11 · VERIFY · RESULT · ALLOW READ. "
            "Порядок: Write implement step → finalize result.yaml (не pending/draft) → @verify → "
            "FAIL/DENY: fix → снова @verify → PASS → FINISH/stop. "
            "Не вызывать @verify повторно после VERDICT: PASS. "
            f"state={json.dumps({k: st.get(k) for k in ('mode','need_verify','verify_done','verify_verdict')})}"
        )
        return

    if finishing and cwd:
        try:
            from session_result import (
                is_finalized_result,
                load_and_normalize_result,
                render_result_template,
                validate_result,
            )

            res, norm_changes = load_and_normalize_result(
                cwd, track="epic", persist=True
            )
            verrs = validate_result(res) if res is not None else []
            not_final = res is not None and not is_finalized_result(res)
            if res is not None and (not_final or verrs):
                # 1st stop → block with fix hint; 2nd (stop_hook_active) → allow
                # so after/normalize/repair-session can run (no infinite stop loop).
                if stop_hook_active:
                    return
                detail = "; ".join(verrs) if verrs else "status pending/draft или вне схемы"
                hint = (
                    "status: ok|blocked|fail|halt|gaps (НЕ pass); "
                    "QA: verdict pass|blocked|fail и status↔verdict "
                    "(pass→ok); draft=false. "
                    f"Шаблон:\n{render_result_template(mode=(st.get('mode') or 'QA').upper())}"
                )
                norm_note = (
                    f" Авто-normalize: {', '.join(norm_changes)}."
                    if norm_changes
                    else ""
                )
                _block(
                    "epic-gate: result.yaml невалиден — "
                    f"{detail}.{norm_note} "
                    "Исправь loop/runtime/epic/result.yaml, затем stop. "
                    f"{hint}"
                    + (
                        " @verify уже PASS — не повторять."
                        if st.get("verify_done") and st.get("verify_verdict") == "PASS"
                        else " Порядок: finalize result.yaml → @verify (если нужен) → FINISH/stop."
                    )
                )
                return
        except Exception:
            pass

    if st.get("need_reviewer") and finishing and not st.get("reviewer_done"):
        if stop_hook_active:
            return
        _block(
            "spawn-gate: BACK QA FINISH без @reviewer запрещён. "
            "Сначала Agent subagent_type=reviewer с Suite results · AC+ · AC− · §0.11 · ALLOW READ. "
            f"state={json.dumps({k: st.get(k) for k in ('mode','need_reviewer','reviewer_done','reviewer_verdict')})}"
        )
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
            _block(
                "spawn-gate: BACK QA FINISH без Handoff QA в memory-bank/activeContext.md. "
                "Перепиши ## Handoff BACK QA … (pass→REFLECT; blocked→BUGFIX) + load_now, "
                "затем остановись."
            )
            return

    if st.get("verify_done") and st.get("verify_verdict") == "FAIL" and finishing:
        if stop_hook_active:
            return
        _block(
            "spawn-gate: verify=FAIL — нельзя FINISH. Исправь blockers, "
            "снова @verify до VERDICT: PASS."
        )
        return

    if not epic_on:
        return

    # EPIC MODE: allow stop only when Handoff/load_now fingerprint advanced.
    progressed, _fp = _epic_progressed(cwd, epic)
    if progressed:
        shape_errs = validate_active_context_shape(read_active_context(cwd))
        if shape_errs:
            if stop_hook_active:
                return
            _block(
                "epic-gate: activeContext shape FAIL — "
                + "; ".join(shape_errs)
                + ". Write весь memory-bank/activeContext.md целиком: "
                "## load_now → ровно 1× ## Handoff → ≤1× ## done. "
                "FORBIDDEN: sandwich/append старых Handoff/done в хвосте."
            )
            return
        st["epic_stop_blocks"] = 0
        save_state(session_id, cwd, st)
        return

    blocks = int(st.get("epic_stop_blocks") or 0) + 1
    st["epic_stop_blocks"] = blocks
    save_state(session_id, cwd, st)
    if blocks >= 3:
        halt_epic(cwd, "stuck without Handoff/load_now progress (stop×3)")
        return

    cmd = epic.get("last_command") or "?"
    _block(
        "epic-gate: нельзя end_turn без прогресса Handoff/load_now в activeContext.md. "
        f"Команда≈{cmd}. Сделай atomic step → Write весь activeContext "
        "(load_now → ровно 1× ## Handoff со строкой `- **Следующий:** …` → ≤1× ## done) → stop. "
        f"Попытка {blocks}/3; дальше epic halt. "
        "FORBIDDEN: остановиться после «начинаю» без FINISH; sandwich Handoff. "
        "Или: python3 .claude/hooks/epic_resolve.py halt --reason '…'"
    )


if __name__ == "__main__":
    main()
