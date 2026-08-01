from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_body_sha256(body: dict[str, Any]) -> str:
    """Return the SHA256 of a stable report body without generated_at."""
    canonical_body = _without_generated_at(body)
    payload = json.dumps(
        canonical_body,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _without_generated_at(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_generated_at(item)
            for key, item in value.items()
            if key != "generated_at"
        }
    if isinstance(value, list):
        return [_without_generated_at(item) for item in value]
    return value
