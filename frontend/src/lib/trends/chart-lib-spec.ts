export type ChartLibId = "uplot";

export const CHART_LIB: ChartLibId = "uplot";

export const CHART_LIB_PACKAGE = "uplot";

export const TREND_CHART_TEST_ID = "trend-chart";

export type ChartMode = "quick" | "extended";

export type ChartQualityBanner = "good" | "partial" | "stale";

export type SeriesPointLike = {
  ts: string;
  value: number | null;
  quality: string;
  min?: number | null;
  max?: number | null;
  samples?: number;
};

export type SetpointBand = {
  id: string;
  label: string;
  value: number;
  kind: "HH" | "H" | "L" | "LL" | "other";
  from_ts?: string;
  to_ts?: string | null;
};

export type EventMarker = {
  id: string;
  ts: string;
  event_name: string;
  severity: "info" | "warning" | "alarm" | "critical";
};

export type TrendChartProps = {
  series: SeriesPointLike[];
  setpoints: SetpointBand[];
  markers: EventMarker[];
  mode: ChartMode;
  onRangeChange: (from: string, to: string) => void;
  quality: ChartQualityBanner;
  resolutionLabel?: string;
  unit?: string;
  tagLabel?: string;
  onMarkerClick?: (markerId: string) => void;
};

export type SeriesRenderKind =
  | "line"
  | "gap"
  | "gap-bad-tick"
  | "quarantine-dotted"
  | "stale-edge";

export function classifyPoint(point: SeriesPointLike): SeriesRenderKind {
  if (point.quality === "stale") {
    return "stale-edge";
  }
  if (point.quality === "quarantine") {
    return "quarantine-dotted";
  }
  if (point.quality === "bad") {
    return "gap-bad-tick";
  }
  if (point.value === null || point.samples === 0) {
    return "gap";
  }
  return "line";
}

export function setpointStrokeToken(kind: SetpointBand["kind"]): string {
  if (kind === "HH" || kind === "LL") {
    return "var(--alarm-critical-fg)";
  }
  if (kind === "H" || kind === "L") {
    return "var(--alarm-warning-fg)";
  }
  return "var(--text-muted)";
}

export function markerSeverityShape(
  severity: EventMarker["severity"],
): "diamond" | "triangle" | "circle" {
  if (severity === "critical" || severity === "alarm") {
    return "diamond";
  }
  if (severity === "warning") {
    return "triangle";
  }
  return "circle";
}

export const PERF_BUDGET = {
  initialRenderMsAt10k: 500,
  zoomRefetchPerceivedMs: 300,
  wsTailFrameMs: 16,
  displayPointsSoftCap: 10_000,
} as const;
