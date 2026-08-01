#!/usr/bin/env python3
"""Epic step YAML — single source for BACK/FRONT (sNN) and INTEG (eNN)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

SCHEMA_EPIC_IMPLEMENT = "epic-implement/v1"
SCHEMA_EPIC_DECOMPOSE = "epic-decompose/v1"
SCHEMA_DECOMPOSE_LEGACY = "integ-decompose/v1"
SCHEMA_IMPLEMENT_LEGACY = "integ-implement/v1"

STEP_S_RE = re.compile(r"(?i)^((?:s)\d{2}-[a-z0-9][a-z0-9-]*)$")
STEP_E_RE = re.compile(r"(?i)^((?:e)\d{2}-[a-z0-9][a-z0-9-]*)$")
_EPIC_MD_ARTIFACT = re.compile(
    r"(?i)(memory-bank/(?:back|front|integration)/implement/implement-[^/]+/(?:[se]\d{2}-[a-z0-9-]+))\.md$"
)


class GrepRow(BaseModel):
    back: str = ""
    front: str = ""


class CheckpointSpec(BaseModel):
    id: str
    criterion: str
    verify: str | None = None

    @field_validator("id")
    @classmethod
    def _id_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^cp\d+$", v):
            raise ValueError(f"checkpoint id must be cpN, got {v!r}")
        return v


class CheckpointProgress(BaseModel):
    id: str
    criterion: str
    status: Literal["pending", "done"] = "pending"
    done_at: str | None = None
    notes: str | None = None

    @field_validator("id")
    @classmethod
    def _id_format(cls, v: str) -> str:
        return v.strip().lower()


class EpicImplementDoc(BaseModel):
    schema_version: str = Field(alias="schema")
    role: Literal["back", "front", "integ"]
    step_id: str
    plan_id: str
    title: str
    status: Literal["in_progress", "completed"]
    implement_index: str
    date: str
    decompose_ref: str | None = None
    element_ref: str | None = None
    task_id: str | None = None
    level: str | None = None
    skills_used: list[str] = Field(default_factory=list)
    discovery: list[str] = Field(default_factory=list)
    gaps: dict[str, Any] | str = Field(default_factory=lambda: {"status": "none"})
    done: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    integration_check: list[str] = Field(default_factory=list)
    grep_control: list[GrepRow] = Field(default_factory=list)
    verification_results: list[str] = Field(default_factory=list)
    checkpoints: list[CheckpointProgress] = Field(default_factory=list)
    resume_from: str | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def _normalize_schema(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        schema = str(out.get("schema") or "")
        if schema == SCHEMA_IMPLEMENT_LEGACY:
            out["schema"] = SCHEMA_EPIC_IMPLEMENT
            out.setdefault("role", "integ")
        if schema == SCHEMA_EPIC_IMPLEMENT and "role" not in out:
            sid = str(out.get("step_id") or "")
            out["role"] = "integ" if sid.lower().startswith("e") else "back"
        if schema == SCHEMA_IMPLEMENT_LEGACY and "decompose_ref" not in out:
            if out.get("element_ref"):
                out["decompose_ref"] = out["element_ref"]
        return out

    @field_validator("schema_version")
    @classmethod
    def _schema_ok(cls, v: str) -> str:
        if v not in {SCHEMA_EPIC_IMPLEMENT, SCHEMA_IMPLEMENT_LEGACY}:
            raise ValueError(f"schema must be {SCHEMA_EPIC_IMPLEMENT!r}")
        return SCHEMA_EPIC_IMPLEMENT


class EpicDecomposeDoc(BaseModel):
    schema_version: str = Field(alias="schema")
    role: Literal["back", "front", "integ"]
    step_id: str
    plan_id: str
    title: str
    next_phase: str
    needs_creative: str | None = None
    goal: str | None = None
    element_id: str | None = None
    ui: dict[str, Any] = Field(default_factory=dict)
    data_need: str | list[str] | None = None
    api_today: list[dict[str, str]] = Field(default_factory=list)
    contract: dict[str, Any] = Field(default_factory=dict)
    db: str | None = None
    back: list[str] = Field(default_factory=list)
    front: list[str] = Field(default_factory=list)
    grep_control: list[GrepRow] = Field(default_factory=list)
    verify: list[str] = Field(default_factory=list)
    tdd: list[str] = Field(default_factory=list)
    checkpoints: list[CheckpointSpec] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    skills: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def _normalize_schema(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        schema = str(out.get("schema") or "")
        if schema == SCHEMA_DECOMPOSE_LEGACY:
            out["schema"] = SCHEMA_EPIC_DECOMPOSE
            out.setdefault("role", "integ")
        if schema == SCHEMA_EPIC_DECOMPOSE and "role" not in out:
            sid = str(out.get("step_id") or "")
            out["role"] = "integ" if sid.lower().startswith("e") else "back"
        return out

    @field_validator("schema_version")
    @classmethod
    def _schema_ok(cls, v: str) -> str:
        if v not in {SCHEMA_EPIC_DECOMPOSE, SCHEMA_DECOMPOSE_LEGACY}:
            raise ValueError(f"schema must be {SCHEMA_EPIC_DECOMPOSE!r}")
        return SCHEMA_EPIC_DECOMPOSE


def step_stem(name: str) -> str | None:
    stem = Path(name).stem.lower()
    if STEP_S_RE.match(stem) or STEP_E_RE.match(stem):
        return stem
    return None


def step_prefix(step_id: str) -> str:
    return "e" if step_id.strip().lower().startswith("e") else "s"


def role_from_path(path: str | Path) -> str | None:
    norm = str(path).replace("\\", "/")
    if "/memory-bank/back/" in norm or norm.startswith("memory-bank/back/"):
        return "back"
    if "/memory-bank/front/" in norm or norm.startswith("memory-bank/front/"):
        return "front"
    if "/memory-bank/integration/" in norm or norm.startswith("memory-bank/integration/"):
        return "integ"
    return None


def role_dir(role: str) -> str:
    r = role.strip().lower()
    if r == "integ":
        return "integration"
    return r


def coerce_epic_artifact_path(
    cwd: str | Path,
    artifact: str | None,
) -> tuple[str | None, str | None]:
    if not artifact:
        return artifact, None
    norm = artifact.replace("\\", "/")
    m = _EPIC_MD_ARTIFACT.search(norm)
    if m:
        yaml_rel = f"{m.group(1)}.yaml"
        if (Path(cwd) / yaml_rel).is_file():
            return yaml_rel, f"artifact {artifact!r}→{yaml_rel!r} (epic yaml canonical)"
    try:
        from epic_shard_extra import coerce_mode_artifact_path

        coerced, msg = coerce_mode_artifact_path(cwd, artifact)
        if msg and coerced:
            return coerced, msg
    except Exception:
        pass
    return artifact, None


def load_yaml_file(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping at root: {path}")
    return data


def load_implement(path: Path) -> EpicImplementDoc:
    return EpicImplementDoc.model_validate(load_yaml_file(path))


def load_decompose(path: Path) -> EpicDecomposeDoc:
    return EpicDecomposeDoc.model_validate(load_yaml_file(path))


def compute_resume_from(checkpoints: list[CheckpointProgress]) -> str | None:
    for cp in checkpoints:
        if cp.status == "pending":
            return cp.id
    return None


def all_checkpoints_done(checkpoints: list[CheckpointProgress]) -> bool:
    if not checkpoints:
        return True
    return all(cp.status == "done" for cp in checkpoints)


def seed_implement_checkpoints(
    decompose: EpicDecomposeDoc,
    existing: list[CheckpointProgress] | None = None,
) -> list[CheckpointProgress]:
    by_id = {cp.id: cp for cp in (existing or [])}
    out: list[CheckpointProgress] = []
    for spec in decompose.checkpoints:
        prev = by_id.get(spec.id)
        if prev:
            out.append(prev)
        else:
            out.append(
                CheckpointProgress(id=spec.id, criterion=spec.criterion, status="pending")
            )
    return out


def _find_shard_file(cwd: str | Path, directory: str, step_id: str) -> Path | None:
    root = Path(cwd)
    d = root / directory
    if not d.is_dir():
        return None
    sid = step_id.strip().lower()
    prefix = "e" if sid.startswith("e") else "s"
    m = re.match(rf"^({prefix}\d{{2}})(?:-.*)?$", sid)
    short = m.group(1) if m else sid
    for ext in (".yaml", ".yml"):
        exact = d / f"{sid}{ext}"
        if exact.is_file():
            return exact
        if m:
            matches = sorted(d.glob(f"{short}-*{ext}"))
            if matches:
                return matches[0]
        exact_short = d / f"{short}{ext}"
        if exact_short.is_file():
            return exact_short
    return None


def resolve_implement_path(
    cwd: str | Path,
    role: str,
    epic_id: str,
    step_id: str,
) -> str:
    rel_dir = f"memory-bank/{role_dir(role)}/implement/implement-{epic_id}"
    found = _find_shard_file(cwd, rel_dir, step_id)
    if found:
        return str(found.relative_to(Path(cwd))).replace("\\", "/")
    stem = step_id.strip().lower()
    p = Path(cwd) / rel_dir / f"{stem}.yaml"
    return str(p.relative_to(Path(cwd))).replace("\\", "/")


def resolve_decompose_path(
    cwd: str | Path,
    role: str,
    epic_id: str,
    step_id: str,
) -> str:
    sub = "plan" if role != "integ" else "plan"
    rel_dir = f"memory-bank/{role_dir(role)}/{sub}/decompose-{epic_id}"
    found = _find_shard_file(cwd, rel_dir, step_id)
    if found:
        return str(found.relative_to(Path(cwd))).replace("\\", "/")
    stem = step_id.strip().lower()
    p = Path(cwd) / rel_dir / f"{stem}.yaml"
    return str(p.relative_to(Path(cwd))).replace("\\", "/")


def find_implement_doc(cwd: str | Path, rel_or_abs: str) -> EpicImplementDoc | None:
    root = Path(cwd)
    p = Path(rel_or_abs)
    if not p.is_absolute():
        p = root / p
    if p.suffix.lower() not in {".yaml", ".yml"} or not p.is_file():
        return None
    try:
        return load_implement(p)
    except Exception:
        return None


def _gaps_ok(gaps: dict[str, Any] | str) -> bool:
    if isinstance(gaps, str):
        return gaps.strip().lower() in {"нет", "none", "no"}
    return str(gaps.get("status", "")).lower() in {"none", "no", "closed"}


def validate_implement_yaml(path: Path, *, finish: bool = True) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing implement file: {path}"]
    try:
        doc = load_implement(path)
    except Exception as exc:
        return [f"invalid epic-implement yaml: {exc}"]

    if doc.role == "integ":
        if not doc.grep_control:
            errors.append("grep_control: at least one row required")
        if not doc.verification_results:
            errors.append("verification_results: at least one entry required")
        if not _gaps_ok(doc.gaps):
            errors.append("gaps: status must be none/нет or {status: none}")
    else:
        if finish and not doc.done:
            errors.append("done: at least one entry required on FINISH")
        if finish and not doc.files:
            errors.append("files: at least one entry required on FINISH")
        if finish and not doc.tests:
            errors.append("tests: at least one entry required on FINISH")
        if finish and not doc.integration_check:
            errors.append("integration_check: at least one entry required on FINISH")

    if doc.role == "integ" and not doc.checkpoints:
        errors.append("checkpoints: at least one checkpoint required for integ")

    if finish:
        if doc.status != "completed":
            errors.append("status must be completed on FINISH")
        for cp in doc.checkpoints:
            if cp.status != "done":
                errors.append(f"checkpoint {cp.id} must be done on FINISH")

    return errors


def validate_decompose_yaml(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing decompose file: {path}"]
    try:
        doc = load_decompose(path)
    except Exception as exc:
        return [f"invalid epic-decompose yaml: {exc}"]
    if not doc.checkpoints:
        errors.append("checkpoints: at least one checkpoint required")
    ids = [cp.id for cp in doc.checkpoints]
    if len(ids) != len(set(ids)):
        errors.append("checkpoints: duplicate id")
    return errors


def validate_shard_yaml(path: Path, *, finish: bool = True, expected_verdict: str | None = None) -> list[str]:
    from epic_shard_extra import detect_shard_kind, validate_epic_shard

    kind = detect_shard_kind(path)
    if kind:
        return validate_epic_shard(path, finish=finish, expected_verdict=expected_verdict)
    norm = str(path).replace("\\", "/")
    if "/implement/implement-" in norm:
        return validate_implement_yaml(path, finish=finish)
    if "/decompose-" in norm and "/plan/" in norm:
        return validate_decompose_yaml(path)
    name = path.name.lower()
    if name.startswith("e") or name.startswith("s"):
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = load_yaml_file(path)
            schema = str(data.get("schema") or "")
            if "implement" in schema or "decompose_ref" in data or "done" in data:
                return validate_implement_yaml(path, finish=finish)
            return validate_decompose_yaml(path)
    return [f"unknown epic yaml path: {path}"]


def checkpoint_prompt_lines(doc: EpicImplementDoc) -> list[str]:
    if not doc.checkpoints:
        return []
    resume = doc.resume_from or compute_resume_from(doc.checkpoints)
    role_label = doc.role.upper()
    lines = [
        "",
        f"## {role_label} checkpoints (HARD)",
        f"Artifact: `{doc.step_id}` — YAML `{SCHEMA_EPIC_IMPLEMENT}`.",
        "Обновляй `checkpoints[].status` → `done` + `done_at` после каждого cp.",
        "Не переделывай cp со status=done.",
    ]
    if resume and doc.status != "completed":
        lines.append(f"**Resume from:** `{resume}` — начни с этого checkpoint.")
    done = [cp.id for cp in doc.checkpoints if cp.status == "done"]
    pending = [cp.id for cp in doc.checkpoints if cp.status == "pending"]
    if done:
        lines.append(f"Done: {', '.join(done)}")
    if pending:
        lines.append(f"Pending: {', '.join(pending)}")
    if all_checkpoints_done(doc.checkpoints) and doc.status != "completed":
        lines.append(
            "Все checkpoints done → finalize status=completed + result.yaml + FINISH."
        )
    lines.append(
        "validate: `python3 .claude/hooks/epic_resolve.py validate-step --path <shard.yaml>`"
    )
    return lines


def format_spec_lines(*, role: str) -> list[str]:
    r = role.strip().lower()
    base = [
        f"FINISH artifact: `.cursor/templates/implement/epic-step.yaml` ({r} YAML):",
        f"schema: {SCHEMA_EPIC_IMPLEMENT}",
        f"role: {r}",
        "обязательные: step_id, plan_id, title, status, implement_index, date, decompose_ref",
        "checkpoints: [{id, criterion, status: pending|done, done_at?, notes?}, ...]",
        "status=completed только когда все checkpoints.status=done (если cp есть)",
        "Самопроверка: `python3 .claude/hooks/epic_resolve.py validate-step --path <shard.yaml>`",
    ]
    if r == "integ":
        base.extend(
            [
                "integ also: element_ref, grep_control, verification_results, gaps",
            ]
        )
    else:
        base.extend(
            [
                f"{r}: done, files, tests, integration_check — обязательны на FINISH",
                "task_id, level — recommended",
            ]
        )
    return base


def implement_completed(cwd: str | Path, rel: str) -> bool:
    p = Path(cwd) / rel
    if not p.is_file() or p.suffix.lower() not in {".yaml", ".yml"}:
        return False
    try:
        doc = load_implement(p)
        return doc.status == "completed" and all_checkpoints_done(doc.checkpoints)
    except Exception:
        return False
