"""Transport plugins must not own API canonical models."""

import ast
from pathlib import Path


PLUGIN_ROOT = Path(__file__).parents[2] / "src" / "collector" / "plugins"
FORBIDDEN_IMPORTS = ("app.telemetry", "app.events")
ALLOWED_MAPPING_MODULES = {
    Path("mqtt/lifecycle_tracker.py"),
    Path("mqtt/mapper.py"),
}


def _python_files() -> list[Path]:
    return sorted(PLUGIN_ROOT.rglob("*.py"))


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_transport_plugins_do_not_import_app_canonical_models() -> None:
    violations = [
        f"{path.relative_to(PLUGIN_ROOT)}: {module}"
        for path in _python_files()
        if path.relative_to(PLUGIN_ROOT) not in ALLOWED_MAPPING_MODULES
        for module in _imports(path)
        if any(module == forbidden or module.startswith(f"{forbidden}.") for forbidden in FORBIDDEN_IMPORTS)
    ]

    assert violations == []
