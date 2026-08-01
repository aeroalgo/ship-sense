"""s20 exclusion scans for the approved v1 runtime surface."""

from pathlib import Path
import re


ROOT = Path(__file__).parents[2]


def test_v1_runtime_excludes_forwarding_and_ml_terms() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for base in (ROOT / "app", ROOT.parent / "edge")
        for path in base.rglob("*.py")
    )

    assert not re.search(r"\b(forwarder|shore_ingest|sklearn|torch)\b", source)
    assert not re.search(r"\bAI\b|ИИ", source)
