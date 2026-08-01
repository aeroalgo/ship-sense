from __future__ import annotations

import os
import subprocess
from pathlib import Path

from apps.edge.storage.backup.coordinator import BackupCoordinator


_ALLOWED_PAYLOADS = {
    "ship-pack/config.yaml": "SHIP_PACK_CONFIG",
    "ship-pack/formulas.yaml": "SHIP_PACK_FORMULAS",
    "ship-pack/warnings.yaml": "SHIP_PACK_WARNINGS",
}


def main() -> None:
    destination = Path(os.environ.get("BACKUP_DIR", "/mnt/backup"))
    pack_dir = Path(os.environ.get("SHIP_PACK_DIR", "/app/ship-pack"))
    payloads: dict[str, bytes] = {}
    for relative_name, variable in _ALLOWED_PAYLOADS.items():
        source = Path(os.environ.get(variable, str(pack_dir / Path(relative_name).name)))
        payloads[relative_name] = source.read_bytes()

    destination.mkdir(parents=True, exist_ok=True)
    events_sql = destination / ".events.sql"
    with events_sql.open("wb") as output:
        subprocess.run(
            ["pg_dump", "--data-only", "--table=events", os.environ["DATABASE_URL"]],
            check=True,
            stdout=output,
        )
    payloads["events.sql"] = events_sql.read_bytes()
    events_sql.unlink()
    BackupCoordinator(destination).publish(payloads)


if __name__ == "__main__":
    main()
