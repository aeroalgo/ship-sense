#!/usr/bin/env python3
"""Backward-compatible re-exports — canonical module: epic_yaml.py."""
from __future__ import annotations

from epic_yaml import (  # noqa: F401
    SCHEMA_EPIC_DECOMPOSE,
    SCHEMA_EPIC_IMPLEMENT,
    CheckpointProgress,
    CheckpointSpec,
    EpicDecomposeDoc,
    EpicImplementDoc,
    GrepRow,
    all_checkpoints_done,
    checkpoint_prompt_lines,
    coerce_epic_artifact_path,
    compute_resume_from,
    find_implement_doc,
    format_spec_lines,
    implement_completed,
    load_decompose,
    load_implement,
    load_yaml_file,
    seed_implement_checkpoints,
    step_stem,
    validate_decompose_yaml,
    validate_implement_yaml,
)
from epic_yaml import resolve_decompose_path as _resolve_decompose_path
from epic_yaml import resolve_implement_path as _resolve_implement_path

SCHEMA_DECOMPOSE = SCHEMA_EPIC_DECOMPOSE
SCHEMA_IMPLEMENT = SCHEMA_EPIC_IMPLEMENT
IntegDecomposeDoc = EpicDecomposeDoc
IntegImplementDoc = EpicImplementDoc

coerce_integ_artifact_path = coerce_epic_artifact_path


def is_integ_step_name(name: str) -> bool:
    stem = step_stem(name)
    return bool(stem and stem.startswith("e"))


def resolve_implement_path(cwd, epic_id: str, step_id: str) -> str:
    return _resolve_implement_path(cwd, "integ", epic_id, step_id)


def resolve_decompose_path(cwd, epic_id: str, step_id: str) -> str:
    return _resolve_decompose_path(cwd, "integ", epic_id, step_id)
