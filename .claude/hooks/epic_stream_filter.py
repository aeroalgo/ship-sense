#!/usr/bin/env python3
"""Print assistant text + tool activity from claude -p --output-format stream-json."""
from __future__ import annotations

import json
import sys
from pathlib import Path


_seen_tool_ids: set[str] = set()


def _write(text: str) -> None:
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except BrokenPipeError:
        sys.exit(0)


def _short_path(path: str) -> str:
    p = path.replace("\\", "/")
    for marker in ("/ship-sense/", "ship-sense/"):
        if marker in p:
            return p.split(marker, 1)[-1]
    return Path(p).name if p else path


def _format_tool(block: dict) -> str:
    name = block.get("name") or "?"
    inp = block.get("input") or {}
    if name == "Read":
        fp = inp.get("file_path") or inp.get("path") or ""
        if fp:
            return f"→ Read {_short_path(fp)}\n"
    if name == "Bash":
        cmd = (inp.get("command") or "").replace("\n", " ").strip()
        if cmd:
            if len(cmd) > 140:
                cmd = cmd[:137] + "..."
            return f"→ Bash {cmd}\n"
    if name in {"Write", "Edit", "MultiEdit"}:
        fp = inp.get("file_path") or inp.get("path") or ""
        if fp:
            return f"→ {name} {_short_path(fp)}\n"
    if name in {"Agent", "Task"}:
        sub = inp.get("subagent_type") or inp.get("agent_type") or ""
        desc = (inp.get("description") or inp.get("prompt") or "")[:80]
        return f"→ {name} {sub} {desc}\n"
    if name == "TaskCreate":
        subj = inp.get("subject") or ""
        return f"→ TaskCreate {subj}\n"
    return f"→ {name}\n"


def _emit_tool(block: dict) -> None:
    tid = block.get("id")
    if tid:
        if tid in _seen_tool_ids:
            return
        _seen_tool_ids.add(tid)
    _write(_format_tool(block))


def _emit_text(text: str) -> None:
    if text:
        _write(text)


def emit_from_obj(obj: dict) -> None:
    if obj.get("type") == "assistant":
        msg = obj.get("message") or {}
        for block in msg.get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                _emit_text(block.get("text") or "")
            elif block.get("type") == "tool_use":
                _emit_tool(block)

    if obj.get("type") == "stream_event":
        ev = obj.get("event") or {}
        et = ev.get("type")
        if et == "content_block_start":
            cb = ev.get("content_block") or {}
            if cb.get("type") == "tool_use" and cb.get("input"):
                _emit_tool(cb)
        elif et == "content_block_delta":
            delta = ev.get("delta") or {}
            if delta.get("type") == "text_delta":
                _emit_text(delta.get("text") or "")

    if obj.get("type") == "content_block_delta":
        delta = obj.get("delta") or {}
        if delta.get("type") == "text_delta":
            _emit_text(delta.get("text") or "")

    if obj.get("type") == "message_delta":
        delta = obj.get("delta") or {}
        for block in delta.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text":
                _emit_text(block.get("text") or "")


def main() -> None:
    _write("--- epic stream (tools + text) ---\n")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            _write(line + "\n")
            continue
        emit_from_obj(obj)
    _write("\n--- epic stream end ---\n")


if __name__ == "__main__":
    main()
