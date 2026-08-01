#!/usr/bin/env python3
"""Epic after_session — extracted from epic_lib.

Dependencies injected by epic_lib (no circular import).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

# Injected by epic_lib
load_epic_state: Callable[..., dict[str, Any]]
save_epic_state: Callable[..., None]
read_active_context: Callable[..., str]
fingerprint_context: Callable[..., str]
extract_handoff_block: Callable[..., str]
validate_active_context_shape: Callable[..., list[str]]
implement_step_from_handoff: Callable[..., str | None]
validate_implement_step_format: Callable[..., list[str]]
command_mode: Callable[..., str | None]
decompose_pending_left: Callable[..., int | None]
assert_integ_yaml_shards: Callable[..., list[str]]
extract_load_now: Callable[..., list[str]]
halt_epic: Callable[..., dict[str, Any]]
complete_epic: Callable[..., dict[str, Any]]
complete_epic_remaining_step: Callable[..., None]
clear_repair_attempt: Callable[..., None]
crosscheck_ok_result: Callable[..., list[str]]
handoff_code_changed_no: Callable[..., bool]
utc_now: Callable[[], str]
HALT_RE: Any
epic_id_from_decompose_path: Callable[..., str]

def after_session(cwd: str | Path) -> dict[str, Any]:
    """Call after claude -p exits: detect progress or halt."""
    st = load_epic_state(cwd)
    if not st.get("active"):
        return {"ok": False, "status": st.get("status"), "reason": "not active"}

    text = read_active_context(cwd)
    fp = fingerprint_context(text)
    before = st.get("pending_fingerprint_before")
    handoff = extract_handoff_block(text)

    shape_errs = validate_active_context_shape(text)
    if shape_errs:
        reason = "activeContext shape FAIL: " + "; ".join(shape_errs)
        st["active"] = False
        st["status"] = "halted"
        st["halt_reason"] = reason
        save_epic_state(cwd, st)
        return {
            "ok": False,
            "status": "halted",
            "reason": reason,
            "fingerprint": fp,
            "shape_errors": shape_errs,
        }

    st["iteration"] = int(st.get("iteration") or 0) + 1
    hist = list(st.get("history") or [])
    hist.append(
        {
            "n": st["iteration"],
            "command": st.get("last_command"),
            "fingerprint": fp,
            "at": utc_now(),
        }
    )
    st["history"] = hist[-50:]

    if before is not None and fp == before:
        st["active"] = False
        st["status"] = "halted"
        st["halt_reason"] = "no Handoff/load_now progress after session"
        save_epic_state(cwd, st)
        return {
            "ok": False,
            "status": "halted",
            "reason": "no progress (same fingerprint)",
            "fingerprint": fp,
        }

    if HALT_RE.search(handoff):
        st["active"] = False
        st["status"] = "halted"
        st["halt_reason"] = "human gate after session"
        save_epic_state(cwd, st)
        return {
            "ok": False,
            "status": "halted",
            "reason": "human gate after session",
            "fingerprint": fp,
        }

    last_mode = command_mode(st.get("last_command") or "") if st.get("last_command") else None
    if last_mode == "IMPLEMENT":
        # Handoff Артефакт = факт сессии; pending мог ошибочно взять следующий sNN
        # из load_now с несколькими шагами — не halt по отсутствующему next-файлу.
        handoff_step = implement_step_from_handoff(handoff)
        pending_step = st.get("pending_implement_step")
        step_rel = handoff_step or pending_step
        if step_rel:
            errs = validate_implement_step_format(Path(cwd) / step_rel)
            if errs:
                reason = f"implement step format FAIL ({step_rel}): " + "; ".join(errs)
                st["active"] = False
                st["status"] = "halted"
                st["halt_reason"] = reason
                save_epic_state(cwd, st)
                return {
                    "ok": False,
                    "status": "halted",
                    "reason": reason,
                    "fingerprint": fp,
                    "pending_implement_step": step_rel,
                    "format_errors": errs,
                    "repairable": True,
                }
        else:
            reason = (
                "implement step format FAIL: не найден step path "
                "(Handoff Артефакт + pending_implement_step пусты)"
            )
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "repairable": True,
            }

    if re.search(r"(?i)—\s*blocked|\bblocked\b", handoff) and re.search(
        r"(?i)Handoff\s+.*\bQA\b", handoff
    ):
        # keep running only if next is BUGFIX — resolve_next will decide
        pass

    st["last_fingerprint"] = fp
    st["status"] = "running"
    st["active"] = True
    saved_pending_step = st.get("pending_implement_step")
    st["pending_implement_step"] = None
    save_epic_state(cwd, st)

    # complete only when next is ARCHIVE (ручной) or last session was REFLECT→ARCHIVE
    pending = decompose_pending_left(cwd, st.get("decompose"))
    load_now = assert_integ_yaml_shards(extract_load_now(text))
    last_mode = command_mode(st.get("last_command") or "") if st.get("last_command") else None

    # Advance canonical ledger via transitions.yaml — result.yaml REQUIRED
    try:
        import loop_engine as le
        from session_result import (
            clear_result,
            collect_test_commands_for_assert,
            load_and_normalize_result,
            pytest_assert_enabled,
            run_test_commands,
            validate_result,
        )

        result_data, norm_changes = load_and_normalize_result(
            cwd, track="epic", persist=True
        )
        if norm_changes:
            le.append_trace(
                cwd,
                {
                    "kind": "result_normalized",
                    "changes": norm_changes,
                    "result": result_data,
                },
                track="epic",
            )
        if not result_data:
            reason = "result.yaml missing (no handoff fallback)"
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            le.append_trace(cwd, {"kind": "halt", "reason": reason}, track="epic")
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "repairable": False,
            }
        if result_data.get("_invalid"):
            reason = f"result.yaml invalid: {result_data.get('_reason')}"
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            le.append_trace(
                cwd,
                {"kind": "halt", "reason": reason, "result": result_data},
                track="epic",
            )
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "repairable": True,
            }
        verrs = validate_result(result_data)
        if verrs:
            reason = "result.yaml validate FAIL: " + "; ".join(verrs)
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            le.append_trace(
                cwd,
                {"kind": "halt", "reason": reason, "result": result_data},
                track="epic",
            )
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "result": result_data,
                "repairable": True,
            }
        try:
            from loop_doctor import foreign_result_errors

            plan_id = None
            if st.get("decompose"):
                plan_id = epic_id_from_decompose_path(str(st["decompose"]))
            role_now = st.get("role_prefix") or result_data.get("role")
            ferrs = foreign_result_errors(
                cwd, role=role_now, plan_id=plan_id, track="epic"
            )
            if ferrs:
                reason = "result.yaml foreign epic FAIL: " + "; ".join(ferrs)
                st["active"] = False
                st["status"] = "halted"
                st["halt_reason"] = reason
                save_epic_state(cwd, st)
                le.append_trace(
                    cwd,
                    {"kind": "halt", "reason": reason, "result": result_data},
                    track="epic",
                )
                return {
                    "ok": False,
                    "status": "halted",
                    "reason": reason,
                    "fingerprint": fp,
                    "result": result_data,
                    "repairable": True,
                }
        except Exception:
            pass
        if result_data.get("status") == "halt":
            halt_epic(cwd, result_data.get("notes") or "result.yaml status=halt")
            return {
                "ok": False,
                "status": "halted",
                "reason": "result.yaml status=halt",
                "fingerprint": fp,
                "result": result_data,
            }

        step_for_check = (
            result_data.get("artifact")
            or implement_step_from_handoff(handoff)
            or saved_pending_step
        )
        # Machine pending queue: pop completed step_id from epic.remaining
        if (
            str(result_data.get("status") or "") == "ok"
            and (last_mode or "").upper() in {"IMPLEMENT", "REFACTOR"}
            and result_data.get("step_id")
        ):
            complete_epic_remaining_step(cwd, str(result_data.get("step_id")))
            pending = decompose_pending_left(cwd, st.get("decompose"))

        xerrs = crosscheck_ok_result(
            cwd,
            result_data,
            last_mode=last_mode,
            decompose=st.get("decompose"),
            step_path=step_for_check,
            handoff=handoff,
            verify_verdict=st.get("last_verify_verdict"),
        )
        if xerrs:
            reason = "result.yaml crosscheck FAIL: " + "; ".join(xerrs)
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            le.append_trace(
                cwd,
                {
                    "kind": "halt",
                    "reason": reason,
                    "result": result_data,
                    "verify_verdict": st.get("last_verify_verdict"),
                },
                track="epic",
            )
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "result": result_data,
                "crosscheck_errors": xerrs,
                "repairable": True,
            }

        if (
            pytest_assert_enabled()
            and str(result_data.get("status") or "") == "ok"
            and (last_mode or "").upper() in {"IMPLEMENT", "REFACTOR", "BUGFIX"}
            and not handoff_code_changed_no(handoff)
        ):
            test_cmds = collect_test_commands_for_assert(
                cwd,
                result_data,
                step_path=step_for_check,
            )
            if not test_cmds:
                reason = (
                    "result.yaml test assert FAIL: нет команд в "
                    "test_commands/pytest_commands / step tests: / ## Тесты "
                    "(status=ok + code_changed≠no)"
                )
                st["active"] = False
                st["status"] = "halted"
                st["halt_reason"] = reason
                save_epic_state(cwd, st)
                le.append_trace(
                    cwd,
                    {"kind": "halt", "reason": reason, "result": result_data},
                    track="epic",
                )
                return {
                    "ok": False,
                    "status": "halted",
                    "reason": reason,
                    "fingerprint": fp,
                    "result": result_data,
                }
            test_errs = run_test_commands(cwd, test_cmds)
            if test_errs:
                reason = "result.yaml test assert FAIL: " + " | ".join(test_errs)
                st["active"] = False
                st["status"] = "halted"
                st["halt_reason"] = reason
                save_epic_state(cwd, st)
                le.append_trace(
                    cwd,
                    {
                        "kind": "halt",
                        "reason": reason,
                        "test_commands": test_cmds,
                        "result": result_data,
                    },
                    track="epic",
                )
                return {
                    "ok": False,
                    "status": "halted",
                    "reason": reason,
                    "fingerprint": fp,
                    "result": result_data,
                    "test_commands": test_cmds,
                }
            le.append_trace(
                cwd,
                {
                    "kind": "test_assert",
                    "ok": True,
                    "test_commands": test_cmds,
                },
                track="epic",
            )

        adv = le.advance_ledger_after_session(
            cwd,
            last_mode=last_mode,
            handoff=handoff,
            role=st.get("role_prefix"),
            pending=pending,
            decompose=st.get("decompose"),
            load_now=load_now,
            model=st.get("model"),
            result=result_data,
            track="epic",
        )
        if not adv.get("ok"):
            reason = adv.get("reason") or "advance_ledger failed"
            st["active"] = False
            st["status"] = "halted"
            st["halt_reason"] = reason
            save_epic_state(cwd, st)
            return {
                "ok": False,
                "status": "halted",
                "reason": reason,
                "fingerprint": fp,
                "result": result_data,
                "event": adv.get("event"),
            }
        ledger_cmd = le.command_from_state(adv.get("state") or {})
        result_source = "result.yaml"
        clear_result(cwd, track="epic")
        if st.get("repair_attempt"):
            st["repair_attempt"] = 0
            save_epic_state(cwd, st)
    except Exception as exc:
        reason = f"after_session ledger error: {exc}"
        st["active"] = False
        st["status"] = "halted"
        st["halt_reason"] = reason
        save_epic_state(cwd, st)
        return {
            "ok": False,
            "status": "halted",
            "reason": reason,
            "fingerprint": fp,
        }

    nxt = ledger_cmd or ""
    mode = command_mode(nxt) if nxt else None

    if pending == 0 and mode == "ARCHIVE":
        complete_epic(cwd, "decompose done — ARCHIVE вручную")
        return {
            "ok": False,
            "status": "complete",
            "reason": "epic complete before ARCHIVE NOW (run manually)",
            "fingerprint": fp,
            "command": ledger_cmd,
            "result_source": result_source,
        }

    if pending == 0 and last_mode == "REFLECT" and mode in {None, "ARCHIVE"}:
        complete_epic(cwd, "REFLECT done — ARCHIVE вручную")
        return {
            "ok": False,
            "status": "complete",
            "reason": "epic complete after REFLECT (ARCHIVE вручную)",
            "fingerprint": fp,
            "result_source": result_source,
        }

    if pending == 0 and mode == "REFLECT":
        return {
            "ok": True,
            "status": "running",
            "reason": "REFLECT next (auto)",
            "fingerprint": fp,
            "pending_steps": pending,
            "ledger_command": ledger_cmd,
            "result_source": result_source,
        }

    return {
        "ok": True,
        "status": "running",
        "reason": "progress ok",
        "fingerprint": fp,
        "pending_steps": pending,
        "ledger_command": ledger_cmd,
        "result_source": result_source,
        "result": result_data,
    }

