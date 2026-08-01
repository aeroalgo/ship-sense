from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.core.dependencies import get_db
from app.core.settings import settings
from app.session.authorization import Permission, require_permission
from apps.edge.storage.raid.status import RaidHealth, parse_zpool_status

router = APIRouter(prefix="/admin/storage", tags=["admin"])


@router.get("", operation_id="getAdminStorage")
async def get_storage(
    _: Annotated[object, Depends(require_permission(Permission.STORAGE_READ))],
    db=Depends(get_db),
) -> dict[str, Any]:
    row = await db.execute(
        text("SELECT disk_total_gb, disk_used_gb, disk_pct, captured_at FROM health_snapshots ORDER BY captured_at DESC LIMIT 1")
    )
    latest = row.mappings().first()
    raid = _raid_status()
    backup = _latest_backup()
    disk_pct = latest["disk_pct"] if latest else None
    degraded = disk_pct is None or float(disk_pct) >= 80.0 or raid["degraded"] or not backup
    return {
        "disk_total_gb": latest["disk_total_gb"] if latest else None,
        "disk_used_gb": latest["disk_used_gb"] if latest else None,
        "disk_pct": disk_pct,
        "raid": raid,
        "backup_last_ok": backup,
        "degraded": degraded,
        "captured_at": latest["captured_at"] if latest else None,
    }


def _raid_status() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["zpool", "status", "-j", settings.STORAGE_RAID_POOL],
            capture_output=True,
            text=True,
            timeout=settings.STORAGE_RAID_COMMAND_TIMEOUT_SEC,
            check=False,
        )
        snapshot = parse_zpool_status(completed.stdout, pool=settings.STORAGE_RAID_POOL)
    except (OSError, subprocess.SubprocessError):
        snapshot = parse_zpool_status("", pool=settings.STORAGE_RAID_POOL)
    return {
        "pool": snapshot.pool,
        "state": snapshot.state,
        "health": snapshot.health,
        "degraded": snapshot.degraded,
        "resilvering": snapshot.resilvering,
        "reason": snapshot.reason,
    }


def _latest_backup() -> bool:
    root = Path(settings.BACKUP_DIR)
    if not root.is_dir():
        return False
    now = datetime.now(timezone.utc)
    for candidate in sorted(root.iterdir(), key=lambda path: path.stat().st_mtime, reverse=True):
        if not candidate.is_dir() or not (candidate / "COMPLETE").is_file():
            continue
        try:
            payload = json.loads((candidate / "manifest.json").read_text(encoding="utf-8"))
            created = datetime.fromisoformat(str(payload["created_at"]).replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            return (now - created).total_seconds() <= settings.BACKUP_MAX_AGE_HOURS * 3600
        except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
            continue
    return False
