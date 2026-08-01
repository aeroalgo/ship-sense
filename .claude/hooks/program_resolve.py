#!/usr/bin/env python3
"""CLI for program-loop: arm / resolve / after / halt / status."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from program_lib import (  # noqa: E402
    after_session,
    arm_program,
    complete_program,
    halt_program,
    load_program_state,
    next_prompt_path,
    parse_gap_queue,
    resolve_next,
    load_gap_file,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="ship-sense program (journey) loop control")
    ap.add_argument("--cwd", default=".", help="repo root")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_arm = sub.add_parser("arm", help="arm program journey")
    p_arm.add_argument("--id", required=True, help="program id, e.g. INTEG-JOURNEY-20260731")
    p_arm.add_argument(
        "--phase",
        default="INTEG_STEPS",
        help="INTEG_PLAN|INTEG_DECOMPOSE|INTEG_STEPS|GAP_FANOUT|…",
    )
    p_arm.add_argument("--integ-decompose", default=None)
    p_arm.add_argument("--integ-plan", default=None)
    p_arm.add_argument("--gap", default=None, help="gap-*.md to seed queue")
    p_arm.add_argument("--resume-implement", default=None)
    p_arm.add_argument("--max", type=int, default=80)
    p_arm.add_argument("--model", default=None)

    sub.add_parser("resolve", help="resolve next action; 0=run, 2=halt, 3=complete")
    p_after = sub.add_parser("after", help="post mode/epic progress")
    p_after.add_argument(
        "--epic-status",
        default=None,
        help="complete|halted when nested epic-loop finished",
    )
    p_halt = sub.add_parser("halt", help="halt program")
    p_halt.add_argument("--reason", default="manual halt")
    sub.add_parser("status", help="print state json")
    sub.add_parser("complete", help="mark complete")
    p_parse = sub.add_parser("parse-gap", help="parse gap md → queue json (dry)")
    p_parse.add_argument("gap")

    args = ap.parse_args()
    cwd = str(Path(args.cwd).resolve())

    if args.cmd == "arm":
        resume = None
        if args.resume_implement:
            resume = {
                "command": "INTEG GAP CLOSE",
                "implement": args.resume_implement,
            }
        st = arm_program(
            cwd,
            program_id=args.id,
            phase=args.phase,
            integ_decompose=args.integ_decompose,
            integ_plan=args.integ_plan,
            gap_path=args.gap,
            resume=resume,
            max_iterations=args.max,
            model=args.model,
        )
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "resolve":
        r = resolve_next(cwd)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        if r.get("ok"):
            action = r.get("action") or {}
            if action.get("kind") == "mode":
                print(f"PROMPT_FILE={next_prompt_path(cwd)}", file=sys.stderr)
            return 0
        if r.get("status") == "complete":
            return 3
        return 2

    if args.cmd == "after":
        r = after_session(cwd, epic_status=args.epic_status)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        if r.get("status") == "complete":
            return 3
        if r.get("status") == "halted" or not r.get("ok"):
            return 2
        return 0

    if args.cmd == "halt":
        st = halt_program(cwd, args.reason)
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "complete":
        st = complete_program(cwd, "manual complete")
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "status":
        st = load_program_state(cwd)
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "parse-gap":
        text = load_gap_file(cwd, args.gap)
        q = parse_gap_queue(text)
        print(json.dumps(q, ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
