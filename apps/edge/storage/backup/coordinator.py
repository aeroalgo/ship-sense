from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from enum import StrEnum
from typing import Mapping


@dataclass(frozen=True, slots=True)
class FileManifest:
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class BackupManifest:
    schema_version: int
    created_at: str
    events_row_count: int | None
    files: dict[str, FileManifest]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "events_row_count": self.events_row_count,
            "files": {
                name: {"size": item.size, "sha256": item.sha256}
                for name, item in self.files.items()
            },
        }


@dataclass(frozen=True, slots=True)
class BackupResult:
    path: Path
    manifest: BackupManifest


class RestoreStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RestoreResult:
    status: str
    code: str | None = None


class BackupCoordinator:
    def __init__(self, destination: str | Path) -> None:
        self.destination = Path(destination)
        self.destination.mkdir(parents=True, exist_ok=True)

    def publish(
        self,
        payloads: Mapping[str, bytes],
        *,
        created_at: datetime | None = None,
        events_row_count: int | None = None,
    ) -> BackupResult:
        timestamp = (created_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
        day = timestamp.date().isoformat()
        staging = Path(tempfile.mkdtemp(prefix=f"{day}.tmp-", dir=self.destination))
        try:
            manifest_files: dict[str, FileManifest] = {}
            for relative_name, content in payloads.items():
                if not isinstance(content, bytes):
                    raise TypeError(f"payload {relative_name!r} must be bytes")
                target = self._safe_path(staging, relative_name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                manifest_files[relative_name] = FileManifest(
                    size=len(content), sha256=hashlib.sha256(content).hexdigest()
                )

            manifest = BackupManifest(
                schema_version=1,
                created_at=timestamp.isoformat(),
                events_row_count=events_row_count,
                files=manifest_files,
            )
            (staging / "manifest.json").write_text(
                json.dumps(manifest.as_dict(), indent=2, sort_keys=True) + "\n"
            )
            (staging / "COMPLETE").write_text("")
            final = self._next_final_path(day)
            os.replace(staging, final)
            return BackupResult(final, manifest)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise

    @staticmethod
    def _safe_path(root: Path, relative_name: str) -> Path:
        candidate = (root / relative_name).resolve()
        if root.resolve() not in candidate.parents:
            raise ValueError(f"payload path escapes backup directory: {relative_name!r}")
        return candidate

    def _next_final_path(self, day: str) -> Path:
        candidate = self.destination / day
        if not candidate.exists():
            return candidate
        index = 2
        while (self.destination / f"{day}-{index}").exists():
            index += 1
        return self.destination / f"{day}-{index}"


def verify_restore(path: str | Path) -> RestoreResult:
    root = Path(path)
    if not (root / "COMPLETE").is_file() or not (root / "manifest.json").is_file():
        return RestoreResult(RestoreStatus.UNKNOWN, "backup_incomplete")
    try:
        manifest = json.loads((root / "manifest.json").read_text())
        for relative_name, expected in manifest["files"].items():
            payload = (root / relative_name).read_bytes()
            if len(payload) != expected["size"] or hashlib.sha256(payload).hexdigest() != expected["sha256"]:
                return RestoreResult(RestoreStatus.FAILED, "checksum_mismatch")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return RestoreResult(RestoreStatus.FAILED, "manifest_invalid")
    return RestoreResult(RestoreStatus.PASSED)
