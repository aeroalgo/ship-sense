#!/usr/bin/env python3
"""CLI for epic-loop: --arm / --resolve / --after / --halt / --status."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from epic_lib import (  # noqa: E402
    EPIC_RESULT_REPAIR_MAX_ATTEMPTS,
    after_session,
    arm_epic,
    complete_epic,
    halt_epic,
    load_epic_state,
    next_prompt_path,
    prepare_result_repair,
    resolve_decompose_arm,
    resolve_next,
)
from epic_yaml import (  # noqa: E402
    compute_resume_from,
    load_implement,
    validate_shard_yaml,
)
from session_resilience import (  # noqa: E402
    detect_abort_in_log,
    git_dirty_paths,
    write_last_session,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="ship-sense epic loop control")
    ap.add_argument("--cwd", default=".", help="repo root")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_arm = sub.add_parser("arm", help="arm epic from decompose path/id")
    p_arm.add_argument("decompose")
    p_arm.add_argument(
        "--role",
        default=None,
        help="BACK|FRONT|INTEG (default: infer from memory-bank path)",
    )
    p_arm.add_argument("--max", type=int, default=40)
    p_arm.add_argument(
        "--model",
        default=None,
        help="exact model id for claude --model (gateway name, full API id)",
    )
    p_arm.add_argument(
        "--from-step",
        default=None,
        help="start queue at sNN/eNN (e.g. e01 or s14)",
    )
    p_arm.add_argument(
        "--force-implement",
        action="store_true",
        help="force next mode IMPLEMENT (ignore Handoff ARCHIVE/REFLECT from other epic)",
    )

    p_res = sub.add_parser(
        "resolve-arm",
        help="resolve decompose → role/track/paths JSON (no arm)",
    )
    p_res.add_argument("decompose")
    p_res.add_argument("--role", default=None)
    p_res.add_argument("--track", default=None)

    sub.add_parser("resolve", help="resolve next prompt; exit 0=run, 2=halt, 3=complete")
    sub.add_parser("after", help="post-session progress check")
    p_repair = sub.add_parser(
        "prepare-repair",
        help="re-activate halted epic for one result.yaml repair session",
    )
    p_repair.add_argument("--reason", default=None)
    p_repair.add_argument(
        "--max-attempts",
        type=int,
        default=EPIC_RESULT_REPAIR_MAX_ATTEMPTS,
    )
    p_validate = sub.add_parser(
        "validate-step",
        help="check epic shard yaml: sNN/eNN/rNN/aNN/qa/decompose",
    )
    p_validate.add_argument(
        "--path",
        required=True,
        help="path to epic shard .yaml (implement/decompose/qa/refactor/security)",
    )
    p_validate.add_argument(
        "--verdict",
        default=None,
        help="expected QA verdict (pass|fail|blocked) for epic-qa crosscheck",
    )
    p_halt = sub.add_parser("halt", help="halt epic")
    p_halt.add_argument("--reason", default="manual halt")
    sub.add_parser("status", help="print state json")
    sub.add_parser("complete", help="mark complete")

    p_flush = sub.add_parser(
        "flush-checkpoint",
        help="mark one implement checkpoint done (mid-step flush)",
    )
    p_flush.add_argument("--path", required=True, help="implement step .yaml")
    p_flush.add_argument("--cp", required=True, help="checkpoint id e.g. cp1")
    p_flush.add_argument(
        "--notes",
        default=None,
        help="optional notes for the checkpoint",
    )

    p_rec = sub.add_parser(
        "record-session",
        help="record last-session.json after claude exit (abort/ok)",
    )
    p_rec.add_argument("--log", required=True, help="session-*.log path")
    p_rec.add_argument("--exit-code", type=int, required=True)
    p_rec.add_argument("--track", default="epic", choices=("epic", "program"))

    args = ap.parse_args()
    cwd = str(Path(args.cwd).resolve())

    if args.cmd == "arm":
        st = arm_epic(
            cwd,
            args.decompose,
            role_prefix=args.role,
            max_iterations=args.max,
            model=args.model,
            from_step=args.from_step,
            force_mode="IMPLEMENT" if args.force_implement else None,
        )
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "resolve-arm":
        r = resolve_decompose_arm(
            cwd,
            args.decompose,
            role=args.role,
            track=args.track,
        )
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "resolve":
        r = resolve_next(cwd)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        if r.get("ok"):
            print(f"PROMPT_FILE={next_prompt_path(cwd)}", file=sys.stderr)
            return 0
        if r.get("status") == "complete":
            return 3
        return 2

    if args.cmd == "after":
        r = after_session(cwd)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        if r.get("status") == "complete":
            return 3
        if r.get("status") == "halted" or not r.get("ok"):
            return 2
        return 0

    if args.cmd == "prepare-repair":
        r = prepare_result_repair(
            cwd,
            args.reason,
            max_attempts=args.max_attempts,
        )
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 2

    if args.cmd == "validate-step":
        rel = args.path.strip()
        step = Path(cwd) / rel
        errors = validate_shard_yaml(
            step,
            finish=True,
            expected_verdict=args.verdict,
        )
        payload = {"ok": not errors, "path": rel, "errors": errors}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] else 2

    if args.cmd == "halt":
        st = halt_epic(cwd, args.reason)
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "complete":
        st = complete_epic(cwd, "manual complete")
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "status":
        st = load_epic_state(cwd)
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "flush-checkpoint":
        import yaml as _yaml
        from datetime import datetime, timezone

        rel = args.path.strip()
        path = Path(cwd) / rel
        if not path.is_file():
            print(json.dumps({"ok": False, "error": f"missing {rel}"}, ensure_ascii=False))
            return 2
        doc = load_implement(path)
        cp_id = args.cp.strip().lower()
        found = False
        for cp in doc.checkpoints:
            if cp.id == cp_id:
                if cp.status == "done":
                    print(
                        json.dumps(
                            {
                                "ok": False,
                                "error": f"{cp_id} already done — не перетирать",
                            },
                            ensure_ascii=False,
                        )
                    )
                    return 2
                cp.status = "done"
                cp.done_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                if args.notes:
                    cp.notes = args.notes
                found = True
                break
        if not found:
            print(
                json.dumps(
                    {"ok": False, "error": f"checkpoint {cp_id} not found"},
                    ensure_ascii=False,
                )
            )
            return 2
        doc.resume_from = compute_resume_from(doc.checkpoints)
        raw = _yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            print(
                json.dumps(
                    {"ok": False, "error": "yaml root must be mapping"},
                    ensure_ascii=False,
                )
            )
            return 2
        by_id = {
            str(c.get("id", "")).lower(): c for c in (raw.get("checkpoints") or [])
        }
        target = by_id.get(cp_id)
        if target is None:
            print(
                json.dumps(
                    {"ok": False, "error": f"raw yaml missing {cp_id}"},
                    ensure_ascii=False,
                )
            )
            return 2
        flushed_cp = next(c for c in doc.checkpoints if c.id == cp_id)
        target["status"] = "done"
        target["done_at"] = flushed_cp.done_at
        if args.notes:
            target["notes"] = args.notes
        raw["resume_from"] = doc.resume_from
        path.write_text(
            _yaml.safe_dump(raw, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "path": rel,
                    "flushed": cp_id,
                    "resume_from": doc.resume_from,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.cmd == "record-session":
        log_path = Path(args.log)
        if not log_path.is_absolute():
            log_path = Path(cwd) / log_path
        abort = detect_abort_in_log(log_path)
        st = load_epic_state(cwd)
        step_id = None
        implement = st.get("pending_implement_step")
        resume_from = None
        if implement:
            doc = load_implement(Path(cwd) / implement)
            step_id = doc.step_id
            resume_from = doc.resume_from or compute_resume_from(doc.checkpoints)
        import loop_engine as le

        ls = le.load_loop_state(cwd)
        step_id = step_id or ((ls.get("step") or {}).get("id"))
        implement = implement or ((ls.get("step") or {}).get("artifact"))
        dirty = git_dirty_paths(cwd)
        interrupted = args.exit_code in (130, 143)
        if abort or interrupted:
            status = "aborted"
            reason = abort or f"process exit {args.exit_code}"
            write_last_session(
                cwd,
                track=args.track,
                status=status,
                reason=reason,
                step_id=step_id,
                implement=implement,
                resume_from=resume_from,
                dirty=dirty,
                log_file=str(log_path),
                exit_code=args.exit_code,
            )
            if args.track == "epic" and st.get("active"):
                halt_epic(cwd, f"session aborted: {reason}")
            payload = {
                "ok": False,
                "status": status,
                "reason": reason,
                "halted": True,
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 2
        write_last_session(
            cwd,
            track=args.track,
            status="ok",
            reason=None,
            step_id=step_id,
            implement=implement,
            resume_from=resume_from,
            dirty=dirty,
            log_file=str(log_path),
            exit_code=args.exit_code,
        )
        print(json.dumps({"ok": True, "status": "ok"}, ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())