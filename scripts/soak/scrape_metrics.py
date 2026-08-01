from __future__ import annotations

import argparse
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from urllib.request import urlopen

_METRIC_RE = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)"
    r"(?:\{(?P<labels>[^}]*)\})?\s+(?P<value>[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)$"
)


@dataclass(frozen=True, slots=True)
class MetricSnapshot:
    timestamp: datetime
    rss_bytes: float | None = None
    write_latency_p99_seconds: float | None = None
    disk_used_ratio: float | None = None
    ws_connections: int | None = None

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["timestamp"] = self.timestamp.isoformat()
        return value


def _parse_labels(raw: str | None) -> dict[str, str]:
    labels: dict[str, str] = {}
    if not raw:
        return labels
    for item in raw.split(","):
        key, separator, value = item.partition("=")
        if separator:
            labels[key.strip()] = value.strip().strip('"')
    return labels


def parse_prometheus(payload: str, *, timestamp: datetime | None = None) -> MetricSnapshot:
    values: dict[str, float] = {}
    for line in payload.splitlines():
        match = _METRIC_RE.match(line.strip())
        if not match:
            continue
        labels = _parse_labels(match.group("labels"))
        name = match.group("name")
        value = float(match.group("value"))
        if name == "process_resident_memory_bytes":
            values["rss_bytes"] = value
        elif name in {"shipsense_write_latency_seconds", "write_latency_seconds"} and labels.get("quantile") == "0.99":
            values["write_latency_p99_seconds"] = value
        elif name in {"shipsense_disk_used_ratio", "disk_used_ratio"}:
            values["disk_used_ratio"] = value
        elif name in {"shipsense_ws_connections", "websocket_connections"}:
            values["ws_connections"] = value
    return MetricSnapshot(
        timestamp=timestamp or datetime.now(timezone.utc),
        rss_bytes=values.get("rss_bytes"),
        write_latency_p99_seconds=values.get("write_latency_p99_seconds"),
        disk_used_ratio=values.get("disk_used_ratio"),
        ws_connections=int(values["ws_connections"]) if "ws_connections" in values else None,
    )


def scrape_metrics(url: str, *, timeout: float = 10.0) -> MetricSnapshot:
    with urlopen(url, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
    return parse_prometheus(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape Prometheus metrics for the T1 soak harness")
    parser.add_argument("url", nargs="?", help="Prometheus endpoint; read stdin when omitted")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    snapshot = scrape_metrics(args.url, timeout=args.timeout) if args.url else parse_prometheus(sys.stdin.read())
    print(snapshot.to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
