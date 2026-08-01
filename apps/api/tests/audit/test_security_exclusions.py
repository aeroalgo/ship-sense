from pathlib import Path
import re


ROOT = Path(__file__).parents[4]


def test_v1_runtime_excludes_shore_forwarding() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert not re.search(r"\b(forwarder|delivery_cursor|shore_ingest)\b", compose)


def test_edge_source_excludes_ml_dependencies_and_prediction() -> None:
    edge_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "apps" / "edge").rglob("*.py")
    )

    assert not re.search(r"\b(sklearn|torch)\b|predict\(", edge_source)


def test_api_errors_exclude_ai_wording() -> None:
    api_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "apps" / "api" / "app").rglob("*.py")
    )

    assert not re.search(r"\bAI\b|ИИ", api_source)


def test_runtime_images_use_non_root_user() -> None:
    dockerfiles = [
        ROOT / "apps" / "api" / "Dockerfile",
        *(ROOT / "apps" / "edge").glob("*/Dockerfile"),
    ]

    assert len(dockerfiles) == 6
    for dockerfile in dockerfiles:
        assert re.search(r"^USER shipsense$", dockerfile.read_text(encoding="utf-8"), re.MULTILINE), dockerfile


def test_security_deliverables_exist() -> None:
    security_dir = ROOT / "docs" / "security"
    required = {
        "threat-model-edge-v1.md",
        "hardening-checklist.md",
        "network-ot-it.md",
        "ota-key-lifecycle.md",
        "ship-access-org-package.md",
    }

    assert required <= {path.name for path in security_dir.iterdir()}
