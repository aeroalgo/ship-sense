from datetime import datetime, timezone

from app.reports.templates import TemplateRenderer


UTC = timezone.utc


def test_watch_uses_one_context_for_json_html_and_collapses_alarms() -> None:
    renderer = TemplateRenderer()
    context = {
        "period": {"from": datetime(2026, 7, 31, 8, tzinfo=UTC), "to": datetime(2026, 7, 31, 16, tzinfo=UTC)},
        "watchkeeper": "<engine-1>",
        "verdict": "good",
        "protections": ["Q5"],
        "alarms": [
            {"event_name": "alarm.HH", "asset_id": "pump-1", "timestamp": "2026-07-31T10:00:00Z"},
            {"event_name": "alarm.HH", "asset_id": "pump-1", "timestamp": "2026-07-31T10:00:10Z"},
        ],
        "debounce_window_sec": 30,
        "provenance": {"official_ts_rule": "watch_explicit", "gaps": []},
    }

    body_json, body_html = renderer.render_report("watch", context)

    assert body_json["alarms_collapsed"][0]["count"] == 2
    assert "<engine-1>" not in body_html
    assert "&lt;engine-1&gt;" in body_html
    assert "watch_explicit" in body_html
    assert body_json["period"]["from"].endswith("Z")


def test_register_requires_waiver_details_when_waived() -> None:
    renderer = TemplateRenderer()

    body_json, body_html = renderer.render_report(
        "register",
        {"status": "waived", "waiver": {"waiver_id": "Q5-001", "reason": "test", "owner": "ops"}},
    )

    assert body_json["waiver"]["waiver_id"] == "Q5-001"
    assert "Q5-001" in body_html


def test_all_report_types_have_versioned_templates() -> None:
    renderer = TemplateRenderer()

    for report_type in ("watch", "daily_noon", "fuel", "register"):
        body_json, body_html = renderer.render_report(report_type, {"provenance": {}})
        assert body_json["type"] == report_type
        assert body_html.startswith("<!doctype html>")
