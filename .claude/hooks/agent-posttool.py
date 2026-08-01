#!/usr/bin/env python3
"""PostToolUse Agent — mark gates from completed subagent content when present."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import (  # noqa: E402
    extract_verdict,
    load_state,
    normalize_type,
    read_stdin,
    save_state,
)


def _text_from_response(resp: object) -> str:
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        parts = []
        for block in resp.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text") or "")
        if parts:
            return "\n".join(parts)
        return json_dumps_safe(resp)
    return str(resp)


def json_dumps_safe(obj: object) -> str:
    import json

    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return str(obj)


def main() -> None:
    data = read_stdin()
    if data.get("tool_name") not in {"Agent", "Task"}:
        return

    tool_input = data.get("tool_input") or {}
    agent_type = normalize_type(
        tool_input.get("subagent_type") or tool_input.get("agent_type")
    )
    resp = data.get("tool_response")
    if isinstance(resp, dict) and resp.get("status") == "async_launched":
        return

    text = _text_from_response(resp)
    verdict = extract_verdict(text)
    if not agent_type or not verdict:
        return

    session_id = data.get("session_id") or ""
    cwd = data.get("cwd") or ""
    st = load_state(session_id, cwd)
    if agent_type == "verify":
        st["verify_done"] = True
        st["verify_verdict"] = verdict
    if agent_type == "reviewer":
        st["reviewer_done"] = True
        st["reviewer_verdict"] = verdict
    save_state(session_id, cwd, st)


if __name__ == "__main__":
    main()
