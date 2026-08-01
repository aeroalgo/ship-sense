from pathlib import Path
from unittest.mock import patch

from apps.edge.storage.backup import runner


def test_runner_allowlists_payloads_and_delegates_to_coordinator(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    pack.mkdir()
    for name, content in {"config.yaml": b"config", "formulas.yaml": b"formulas", "warnings.yaml": b"warnings"}.items():
        (pack / name).write_bytes(content)

    class Completed:
        def __init__(self, *_args, **_kwargs):
            pass

    captured = {}

    class FakeCoordinator:
        def __init__(self, destination):
            captured["destination"] = destination

        def publish(self, payloads):
            captured["payloads"] = payloads

    with patch.dict("os.environ", {"DATABASE_URL": "postgres://db", "BACKUP_DIR": str(tmp_path / "backup"), "SHIP_PACK_DIR": str(pack)}), patch.object(runner.subprocess, "run", Completed), patch.object(runner, "BackupCoordinator", FakeCoordinator):
        runner.main()

    assert captured["payloads"]["events.sql"] == b""
    assert set(captured["payloads"]) == {"events.sql", "ship-pack/config.yaml", "ship-pack/formulas.yaml", "ship-pack/warnings.yaml"}
