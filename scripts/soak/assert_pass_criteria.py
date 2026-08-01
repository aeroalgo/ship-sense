from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Iterable

from scripts.soak.scrape_metrics import MetricSnapshot


@dataclass(frozen=True, slots=True)
class PassCriteriaResult:
    passed: bool
    memory_slope_percent_per_day: float | None
    write_latency_p99_seconds: float | None
    max_disk_used_ratio: float | None
    max_ws_connections: int | None
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self) | {"failures": list(self.failures)}


def _memory_slope_percent_per_day(snapshots: list[MetricSnapshot]) -> float | None:
    first = snapshots[0]
    last = snapshots[-1]
    if first.rss_bytes is None or last.rss_bytes is None or first.rss_bytes <= 0:
        return None
    elapsed_days = (last.timestamp - first.timestamp).total_seconds() / 86_400
    if elapsed_days <= 0:
        return None
    return (last.rss_bytes - first.rss_bytes) / first.rss_bytes * 100 / elapsed_days


def assert_pass_criteria(
    snapshots: Iterable[MetricSnapshot],
    *,
    max_memory_slope_percent_per_day: float = 1.0,
    max_write_latency_p99_seconds: float = 1.0,
    max_disk_used_ratio: float = 0.90,
) -> PassCriteriaResult:
    ordered = sorted(snapshots, key=lambda snapshot: snapshot.timestamp)
    failures: list[str] = []
    if len(ordered) < 2:
        failures.append("insufficient_samples")
        memory_slope = None
    else:
        memory_slope = _memory_slope_percent_per_day(ordered)
        if memory_slope is None:
            failures.append("memory_slope_unavailable")
        elif memory_slope >= max_memory_slope_percent_per_day:
            failures.append("memory_slope")

    latencies = [item.write_latency_p99_seconds for item in ordered if item.write_latency_p99_seconds is not None]
    write_latency = max(latencies) if latencies else None
    if write_latency is None:
        failures.append("write_latency_unavailable")
    elif write_latency > max_write_latency_p99_seconds:
        failures.append("write_latency_p99")

    disks = [item.disk_used_ratio for item in ordered if item.disk_used_ratio is not None]
    max_disk = max(disks) if disks else None
    if max_disk is None:
        failures.append("disk_used_unavailable")
    elif max_disk > max_disk_used_ratio:
        failures.append("disk_used_ratio")

    connections = [item.ws_connections for item in ordered if item.ws_connections is not None]
    max_connections = max(connections) if connections else None
    if max_connections is None:
        failures.append("ws_connections_unavailable")

    return PassCriteriaResult(
        passed=not failures,
        memory_slope_percent_per_day=memory_slope,
        write_latency_p99_seconds=write_latency,
        max_disk_used_ratio=max_disk,
        max_ws_connections=max_connections,
        failures=tuple(failures),
    )


def _load_snapshots(stream: Iterable[str]) -> list[MetricSnapshot]:
    snapshots: list[MetricSnapshot] = []
    for line in stream:
        if not line.strip():
            continue
        value = ast.literal_eval(line) if line.lstrip().startswith("MetricSnapshot(") else json.loads(line)
        if isinstance(value, MetricSnapshot):
            snapshots.append(value)
            continue
        value["timestamp"] = datetime.fromisoformat(value["timestamp"])
        snapshots.append(MetricSnapshot(**value))
    return snapshots


def main() -> int:
    parser = argparse.ArgumentParser(description="Assert T1 soak pass criteria")
    parser.add_argument("path", nargs="?", help="JSON-lines snapshot file; read stdin when omitted")
    parser.add_argument("--max-memory-slope", type=float, default=1.0)
    parser.add_argument("--max-write-latency", type=float, default=1.0)
    parser.add_argument("--max-disk-used", type=float, default=0.90)
    args = parser.parse_args()
    stream = open(args.path, encoding="utf-8") if args.path else sys.stdin
    try:
        result = assert_pass_criteria(
            _load_snapshots(stream),
            max_memory_slope_percent_per_day=args.max_memory_slope,
            max_write_latency_p99_seconds=args.max_write_latency,
            max_disk_used_ratio=args.max_disk_used,
        )
    finally:
        if args.path:
            stream.close()
    print(json.dumps(result.to_dict(), default=str))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
