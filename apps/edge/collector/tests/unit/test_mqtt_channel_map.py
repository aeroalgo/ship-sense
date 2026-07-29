from pathlib import Path

from collector.plugins.mqtt.channel_map import MqttChannelMap


MAPS_DIR = Path(__file__).parents[2] / "config" / "maps"


def test_aps_map_loads_known_analog_channel() -> None:
    channel_map = MqttChannelMap.load(MAPS_DIR / "mqtt_channels_aps.yaml")

    entry = channel_map.lookup("APS.TAI4101")

    assert entry is not None
    assert entry.tag_id == "TAI4101"
    assert entry.kind == "analog"
    assert entry.unit == "degC"
    assert entry.thresholds.expose is True


def test_unknown_channel_returns_none() -> None:
    channel_map = MqttChannelMap.load(MAPS_DIR / "mqtt_channels_aps.yaml")

    assert channel_map.lookup("APS.UNKNOWN") is None


def test_geu_map_loads_egt_group_channel() -> None:
    channel_map = MqttChannelMap.load(MAPS_DIR / "mqtt_channels_geu.yaml")

    entry = channel_map.lookup("GEU.EGT1")

    assert entry is not None
    assert entry.tag_id == "GEU.EGT1"
    assert entry.kind == "egt_group"
    assert entry.unit == "degC"


def test_map_rejects_duplicate_channel_ids(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.yaml"
    path.write_text(
        "channels:\n"
        "  - channel_id: APS.TAI4101\n"
        "    tag_id: TAI4101\n"
        "    kind: analog\n"
        "  - channel_id: APS.TAI4101\n"
        "    tag_id: TAI4102\n"
        "    kind: analog\n",
        encoding="utf-8",
    )

    try:
        MqttChannelMap.load(path)
    except ValueError as exc:
        assert "duplicate channel_id" in str(exc)
    else:
        raise AssertionError("duplicate channel_id must be rejected")
