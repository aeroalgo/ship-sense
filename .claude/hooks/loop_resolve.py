#!/usr/bin/env python3
"""CLI for canonical loop-state + transitions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loop_engine import (  # noqa: E402
    apply_event,
    command_from_state,
    load_loop_state,
    load_transitions,
    match_transition,
    render_transitions_mermaid,
    sync_from_handoff,
    validate_transitions_graph,
)
import epic_lib as el  # noqa: E402
from session_result import (  # noqa: E402
    clear_result,
    load_result,
    render_result_template,
    save_result,
    validate_result,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="ship-sense loop-state / transitions")
    ap.add_argument("--cwd", default=".", help="repo root")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="print loop-state.yaml as JSON")
    sub.add_parser("command", help="print next command from loop-state")
    p_sync = sub.add_parser("sync", help="sync loop-state from activeContext Handoff (diag)")
    p_sync.add_argument("--decompose", default=None)
    p_apply = sub.add_parser("apply", help="apply transition event")
    p_apply.add_argument("event")
    p_match = sub.add_parser("match", help="show which transition would fire")
    p_match.add_argument("event")
    sub.add_parser("transitions", help="list transition ids")
    p_graph = sub.add_parser("graph", help="validate / render transitions graph")
    p_graph.add_argument(
        "--check",
        action="store_true",
        help="validate transitions.yaml (exit 1 on errors)",
    )
    p_graph.add_argument(
        "--mermaid",
        action="store_true",
        help="print mermaid stateDiagram from transitions",
    )
    p_result = sub.add_parser("result", help="show/write/clear session result.yaml")
    p_result.add_argument("--track", default="epic", choices=("epic", "program"))
    p_result.add_argument("--clear", action="store_true")
    p_result.add_argument("--template", action="store_true", help="print YAML template")
    p_result.add_argument("--status", default=None)
    p_result.add_argument("--verdict", default=None)
    p_result.add_argument("--step-id", default=None)
    p_result.add_argument("--mode", default=None)

    args = ap.parse_args()
    cwd = str(Path(args.cwd).resolve())

    if args.cmd == "status":
        print(json.dumps(load_loop_state(cwd), ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "command":
        print(command_from_state(load_loop_state(cwd)) or "")
        return 0

    if args.cmd == "sync":
        text = el.read_active_context(cwd)
        st = sync_from_handoff(
            cwd,
            el.extract_handoff_block(text),
            load_now=el.extract_load_now(text),
            decompose=args.decompose,
            pending=el.decompose_pending_left(cwd, args.decompose) if args.decompose else None,
            save=True,
        )
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "apply":
        r = apply_event(cwd, args.event)
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
        return 0 if r.get("ok") else 2

    if args.cmd == "match":
        st = load_loop_state(cwd)
        row = match_transition(cwd, st, args.event)
        print(json.dumps(row, ensure_ascii=False, indent=2))
        return 0 if row else 1

    if args.cmd == "transitions":
        tr = load_transitions(cwd)
        for row in tr.get("transitions") or []:
            print(row.get("id"), "on=", row.get("on"), "when=", row.get("when"))
        return 0

    if args.cmd == "graph":
        if args.mermaid:
            print(render_transitions_mermaid(cwd), end="")
            if not args.check:
                return 0
        report = validate_transitions_graph(cwd)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.check or not args.mermaid:
            return 0 if report.get("ok") else 1
        return 0

    if args.cmd == "result":
        track = args.track
        if args.template:
            print(
                render_result_template(
                    status=args.status or "ok",
                    verdict=args.verdict,
                    step_id=args.step_id,
                    mode=args.mode,
                ),
                end="",
            )
            return 0
        if args.clear:
            cleared = clear_result(cwd, track=track)
            print(json.dumps({"cleared": cleared, "track": track}))
            return 0
        if args.status:
            path = save_result(
                cwd,
                {
                    "status": args.status,
                    "verdict": args.verdict,
                    "step_id": args.step_id,
                    "mode": args.mode,
                },
                track=track,
            )
            data = load_result(cwd, track=track)
            print(
                json.dumps(
                    {"path": str(path), "result": data, "errors": validate_result(data)},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0 if not validate_result(data or {}) else 2
        data = load_result(cwd, track=track)
        print(
            json.dumps(
                {
                    "track": track,
                    "result": data,
                    "errors": validate_result(data) if data else ["missing"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if data and not validate_result(data) else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
