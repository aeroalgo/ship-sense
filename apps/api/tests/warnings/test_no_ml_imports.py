from pathlib import Path


WARNING_ROOT = Path(__file__).parents[2] / "app" / "warnings"


def test_warning_package_has_no_ml_or_ai_imports() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in WARNING_ROOT.glob("*.py"))
    lowered = source.lower()
    assert "sklearn" not in lowered
    assert "torch" not in lowered
    assert "tensorflow" not in lowered
    assert " ai " not in lowered


def test_warning_schema_has_no_ai_strings() -> None:
    source = (WARNING_ROOT / "schemas.py").read_text(encoding="utf-8").lower()
    assert " ai " not in source
    assert "искусствен" not in source
