from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from collector.config.models import CollectorSettings, SourceConfig, TagMapEntry

DEFAULT_SOURCES_PATH = Path("config/sources.dev.yaml")
DEFAULT_MAPS_DIR = Path("maps")


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    except OSError as exc:
        raise FileNotFoundError(f"Configuration file not found: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Configuration root must be a mapping: {path}")
    return data


def sources_path(path: str | Path | None = None) -> Path:
    return Path(path or os.getenv("COLLECTOR_SOURCES_PATH") or DEFAULT_SOURCES_PATH)


def maps_dir(path: str | Path | None = None) -> Path:
    return Path(path or os.getenv("COLLECTOR_MAPS_DIR") or DEFAULT_MAPS_DIR)


def load_settings(path: str | Path | None = None) -> CollectorSettings:
    return CollectorSettings.model_validate(_read_yaml(sources_path(path)))


def load_sources(path: str | Path | None = None) -> list[SourceConfig]:
    return load_settings(path).sources


def load_tag_map(path: str | Path) -> list[TagMapEntry]:
    data = _read_yaml(Path(path))
    entries = data.get("tags", data.get("nodes", []))
    if not isinstance(entries, list):
        raise ValueError(f"Tag map entries must be a list: {path}")
    return [TagMapEntry.model_validate(entry) for entry in entries]
