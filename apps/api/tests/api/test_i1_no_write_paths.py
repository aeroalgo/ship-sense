import ast
from pathlib import Path


API_ROOT = Path(__file__).parents[2] / "app"
FORBIDDEN_IMPORT_PREFIXES = ("pymodbus", "asyncua")


def _python_files() -> list[Path]:
    return sorted(API_ROOT.rglob("*.py"))


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _is_forbidden_import(module: str) -> bool:
    if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
        return True
    return module.startswith("collector.plugins.") and ".connector" in module


def test_api_does_not_import_connector_write_paths() -> None:
    violations = [
        f"{path.relative_to(API_ROOT)}: {module}"
        for path in _python_files()
        for module in _imports(path)
        if _is_forbidden_import(module)
    ]

    assert violations == []
