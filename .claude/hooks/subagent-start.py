#!/usr/bin/env python3
"""SubagentStart — inject per-agent contract into child context."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lib import CONTRACTS, HARD_RULE, emit, normalize_type, read_stdin  # noqa: E402


def main() -> None:
    data = read_stdin()
    agent_type = normalize_type(data.get("agent_type")) or data.get("agent_type")
    contract = CONTRACTS.get(agent_type or "", "")
    if not contract:
        return
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": f"{contract}\n{HARD_RULE}",
            }
        }
    )


if __name__ == "__main__":
    main()
