from pathlib import Path

import pytest

from app.warnings.config import BASELINE_TAGS, load_warning_config


ROOT = Path(__file__).parents[4]


def test_production_config_has_bounded_explicit_snapshot() -> None:
    config = load_warning_config(ROOT / "ship-pack" / "makarov" / "warnings.yaml", set(BASELINE_TAGS))
    assert len(config.tags) == 53
    assert tuple(tag.tag_id for tag in config.tags) == BASELINE_TAGS
    assert config.tags[-1].comparison == "low"


def test_unknown_tag_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "warnings.yaml"
    path.write_text('version: "1"\ndefaults: {}\ntags:\n  - tag_id: TAI9999\n', encoding="utf-8")
    with pytest.raises(ValueError, match="unknown warning tag"):
        load_warning_config(path, set(BASELINE_TAGS))
