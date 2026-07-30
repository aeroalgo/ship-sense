"""Storage must consume canonical models from the API package."""

import ast
from pathlib import Path


STORAGE_ROOT = Path(__file__).parents[2] / "apps/edge/storage"
FORBIDDEN_PREFIX = "collector.domain"


def _python_files() -> list[Path]:
    return sorted(STORAGE_ROOT.rglob("*.py"))


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_storage_does_not_import_collector_domain() -> None:
    violations = [
        f"{path.relative_to(STORAGE_ROOT)}: {module}"
        for path in _python_files()
        for module in _imports(path)
        if module == FORBIDDEN_PREFIX or module.startswith(f"{FORBIDDEN_PREFIX}.")
    ]

    assert violations == []
