from __future__ import annotations

from pathlib import Path


def test_compression_migration_uses_if_not_exists() -> None:
    path = Path("migrations/versions/006_compression_retention.py")
    text = path.read_text(encoding="utf-8")
    assert "if_not_exists => true" in text
    assert "add_compression_policy" in text
    assert "add_retention_policy" in text
