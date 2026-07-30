from pathlib import Path

import pytest
from pydantic import ValidationError

from collector.config.loader import load_sources
from collector.config.validator import validate_config
from collector.domain.errors import ConfigError


FIXTURE = Path(__file__).parents[1] / "fixtures" / "config" / "mqtt_sources.yaml"


def test_mqtt_sources_load_with_defaults() -> None:
    sources = load_sources(FIXTURE)

    assert [source.id for source in sources] == ["panel_aps", "panel_geu"]
    assert sources[0].protocol == "mqtt"
    assert sources[0].subscribe is not None
    assert sources[0].subscribe.qos == 1
    assert sources[0].options.publish_allowed is False
    assert sources[0].connection.host == "mqtt-broker"


def test_mqtt_publish_is_rejected_in_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLLECTOR_PROFILE", "prod")
    sources = load_sources(FIXTURE)
    sources[0].options.publish_allowed = True

    with pytest.raises(ConfigError, match="publish_allowed.*prod"):
        validate_config(sources, maps_root=FIXTURE.parent, profile="prod")


def test_unknown_mqtt_field_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown_field"):
        load_sources(FIXTURE.parent / "mqtt_sources_unknown_field.yaml")


def test_docker_compose_mqtt_maps_dir() -> None:
    import yaml
    compose_path = Path(__file__).parents[5] / "docker-compose.yml"
    assert compose_path.exists(), f"docker-compose.yml not found at {compose_path}"
    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)
    
    collector_mqtt = compose_data.get("services", {}).get("collector-mqtt", {})
    env = collector_mqtt.get("environment", {})
    assert env.get("COLLECTOR_MAPS_DIR") == "/app/maps"
