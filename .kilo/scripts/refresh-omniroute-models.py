#!/usr/bin/env python3
"""Refresh OmniRoute model catalog in ~/.config/kilo/kilo.jsonc"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

GLOBAL = Path.home() / ".config/kilo/kilo.jsonc"
SIDE = Path(__file__).resolve().parents[1] / "omniroute-models.generated.json"
BASE = "http://localhost:20128/v1"


def limits(mid: str) -> dict:
    low = mid.lower()
    if any(x in low for x in ("luna", "sol", "terra")):
        return {"context": 300000, "output": 65536}
    if "flash" in low or "lite" in low:
        return {"context": 128000, "output": 16384}
    if "grok" in low or "glm" in low:
        return {"context": 200000, "output": 32768}
    return {"context": 200000, "output": 32768}


def main() -> None:
    with urllib.request.urlopen(f"{BASE}/models", timeout=15) as r:
        data = json.load(r)
    ids = sorted({m["id"] for m in data.get("data", []) if isinstance(m, dict) and m.get("id")})
    models = {
        mid: {"id": mid, "name": mid, "tool_call": True, "limit": limits(mid)} for mid in ids
    }
    preferred = [
        "cx/gpt-5.6-luna",
        "gc/grok-build",
        "glm/glm-5.2",
        "antigravity/gemini-3.5-flash-high",
        "antigravity/gemini-3.5-flash-low",
    ]
    default = next((p for p in preferred if p in models), ids[0])

    cfg = {
        "$schema": "https://app.kilo.ai/config.json",
        "model": f"omniroute/{default}",
        "provider": {
            "omniroute": {
                "name": "OmniRoute",
                "npm": "@ai-sdk/openai-compatible",
                "api": BASE,
                "options": {
                    "baseURL": BASE,
                    "apiKey": "{file:/home/aero/.codex/.omniroute_key}",
                    "timeout": 600000,
                },
                "models": models,
            }
        },
    }
    GLOBAL.parent.mkdir(parents=True, exist_ok=True)
    GLOBAL.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")
    SIDE.write_text(
        json.dumps(
            {"default": default, "count": len(models), "preferred": preferred, "ids": ids},
            indent=2,
        )
        + "\n"
    )
    print(f"ok models={len(models)} default={default} -> {GLOBAL}")


if __name__ == "__main__":
    main()
