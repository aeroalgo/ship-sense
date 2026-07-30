"""Import ownership checks for API domain modules."""

import ast
from pathlib import Path


DOMAIN_ROOT = Path(__file__).parents[2] / "app"
DOMAIN_PACKAGES = ("telemetry", "events", "semantic")
FORBIDDEN_IMPORTS = ("fastapi", "starlette", "app.api", "app.main")


def _python_files(package: str) -> list[Path]:
    return sorted((DOMAIN_ROOT / package).rglob("*.py"))


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_api_domain_modules_do_not_import_http_layers() -> None:
    violations = [
        f"{path.relative_to(DOMAIN_ROOT.parent)}: {module}"
        for package in DOMAIN_PACKAGES
        for path in _python_files(package)
        for module in _imports(path)
        if any(module == forbidden or module.startswith(f"{forbidden}.") for forbidden in FORBIDDEN_IMPORTS)
    ]

    assert violations == []
