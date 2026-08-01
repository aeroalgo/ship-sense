from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any, Literal

ReportType = Literal["watch", "daily_noon", "fuel", "register"]


class TemplateRenderer:
    def render_report(self, report_type: ReportType, context: dict[str, Any]) -> tuple[dict[str, Any], str]:
        normalized = _normalize(context)
        normalized["type"] = report_type
        if report_type == "watch":
            normalized["alarms_collapsed"] = _collapse_alarms(
                normalized.get("alarms", []), normalized.get("debounce_window_sec", 0)
            )
        if report_type == "register" and normalized.get("status") == "waived":
            _validate_waiver(normalized.get("waiver"))
        body_json = normalized
        return body_json, _render_html(report_type, normalized)


def _normalize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def _collapse_alarms(alarms: list[dict[str, Any]], window_sec: int) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
    for alarm in alarms:
        groups.setdefault((alarm.get("event_name"), alarm.get("asset_id")), []).append(alarm)
    collapsed = []
    for (event_name, asset_id), items in groups.items():
        items = sorted(items, key=lambda item: item.get("timestamp", ""))
        current = [items[0]]
        for item in items[1:]:
            if _within_window(current[-1].get("timestamp"), item.get("timestamp"), window_sec):
                current.append(item)
            else:
                collapsed.append(_alarm_group(event_name, asset_id, current))
                current = [item]
        collapsed.append(_alarm_group(event_name, asset_id, current))
    return collapsed


def _within_window(previous: Any, current: Any, window_sec: int) -> bool:
    if not previous or not current:
        return False
    try:
        left = datetime.fromisoformat(str(previous).replace("Z", "+00:00"))
        right = datetime.fromisoformat(str(current).replace("Z", "+00:00"))
    except ValueError:
        return False
    return (right - left).total_seconds() <= window_sec


def _alarm_group(event_name: Any, asset_id: Any, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"event_name": event_name, "asset_id": asset_id, "count": len(items), "first_timestamp": items[0].get("timestamp")}


def _validate_waiver(waiver: Any) -> None:
    if not isinstance(waiver, dict) or not all(waiver.get(field) for field in ("waiver_id", "reason", "owner")):
        raise ValueError("waived register requires waiver_id, reason and owner")


def _render_html(report_type: str, context: dict[str, Any]) -> str:
    title = {"watch": "Вахтенная сводка", "daily_noon": "Полуденный отчёт", "fuel": "Отчёт по топливу", "register": "Реестр"}[report_type]
    provenance = context.get("provenance", {})
    details = html.escape(json.dumps(context, ensure_ascii=False, default=str))
    waiver = context.get("waiver", {})
    waiver_html = f'<p class="waiver">Исключение: {html.escape(str(waiver.get("waiver_id", "")))}</p>' if report_type == "register" and context.get("status") == "waived" else ""
    return f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>{title}</title></head><body><main><h1>{title}</h1><div data-report-type="{report_type}">{details}</div><section class="provenance"><h2>Происхождение данных</h2><p>{html.escape(str(provenance.get("official_ts_rule", "")))}</p></section>{waiver_html}</main></body></html>'
