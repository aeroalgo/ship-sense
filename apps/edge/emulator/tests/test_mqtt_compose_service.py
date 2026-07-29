from __future__ import annotations

from pathlib import Path

import yaml

COMPOSE_PATH = Path(__file__).resolve().parents[4] / "docker-compose.yml"


def _emulator_mqtt_service() -> dict:
    compose = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))
    return compose["services"]["emulator-mqtt"]


def test_emulator_mqtt_entrypoint_invokes_mqtt_publish_not_modbus_main() -> None:
    service = _emulator_mqtt_service()
    entrypoint = service.get("entrypoint")
    assert entrypoint == ["python", "-m", "emulator.mqtt_publish"], (
        "emulator-mqtt must override image ENTRYPOINT (python -m emulator); "
        f"got {entrypoint!r}"
    )
    command = service.get("command") or []
    assert command[:1] != ["python"], (
        "command must be mqtt_publish CLI args only, not another python -m …; "
        f"got {command!r}"
    )
    assert "--broker" in command
    assert "--panels" in command


def test_smoke_dual_probes_health_via_exec_not_run() -> None:
    script = (
        Path(__file__).resolve().parents[4] / "scripts" / "smoke-mqtt-stack.sh"
    ).read_text(encoding="utf-8")
    assert "exec -T collector-mqtt python -c" in script
    assert "run --rm --no-deps collector-mqtt python -c" not in script
