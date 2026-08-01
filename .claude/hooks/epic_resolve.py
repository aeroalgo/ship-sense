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
from epic_yaml import validate_shard_yaml  # noqa: E402


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

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
