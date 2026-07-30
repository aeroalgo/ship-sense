from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure pytest-asyncio plugin is loaded for async fixtures/tests in strict mode.
# pyproject.toml sets asyncio_mode = "strict", but explicit registration guarantees
# hooks are active even if entry-point discovery is affected by PYTHONPATH manipulation.
pytest_plugins = ["pytest_asyncio"]


ROOT = Path(__file__).resolve().parents[1]
for source_dir in (ROOT / "apps/edge/collector/src", ROOT / "apps/edge/emulator/src"):
    source = str(source_dir)
    if source not in sys.path:
        sys.path.insert(0, source)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: storage integration tests")
    config.addinivalue_line("markers", "load: storage throughput tests")
    config.addinivalue_line("markers", "e2e: end-to-end pipeline tests (compose or external dependencies)")
