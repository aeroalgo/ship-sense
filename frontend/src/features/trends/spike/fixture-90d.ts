import type {
  EventMarker,
  SeriesPointLike,
  SetpointBand,
} from "@/lib/trends/chart-lib-spec";

const MINUTE_MS = 60_000;

export type SpikeFixture = {
  series: SeriesPointLike[];
  setpoints: SetpointBand[];
  markers: EventMarker[];
  meta: {
    days: number;
    stepMinutes: number;
    pointCount: number;
    gapCount: number;
  };
};

export function buildSpikeFixture(options?: {
  days?: number;
  stepMinutes?: number;
  endTs?: number;
}): SpikeFixture {
  const days = options?.days ?? 90;
  const stepMinutes = options?.stepMinutes ?? 10;
  const endTs = options?.endTs ?? Date.UTC(2026, 6, 26, 12, 0, 0);
  const startTs = endTs - days * 24 * 60 * MINUTE_MS;
  const stepMs = stepMinutes * MINUTE_MS;

  const series: SeriesPointLike[] = [];
  let gapCount = 0;

  for (let t = startTs; t <= endTs; t += stepMs) {
    const i = series.length;
    const hour = new Date(t).getUTCHours();
    const isGapBlock = hour === 3 && i % 7 === 0;
    const isBad = i % 211 === 0;
    const isQuarantine = i % 307 === 0;

    if (isGapBlock) {
      series.push({
        ts: new Date(t).toISOString(),
        value: null,
        quality: "good",
        samples: 0,
      });
      gapCount += 1;
      continue;
    }

    if (isBad) {
      series.push({
        ts: new Date(t).toISOString(),
        value: null,
        quality: "bad",
        samples: 0,
      });
      gapCount += 1;
      continue;
    }

    const base = 42 + Math.sin(i / 40) * 8 + Math.sin(i / 400) * 3;
    series.push({
      ts: new Date(t).toISOString(),
      value: Number(base.toFixed(2)),
      quality: isQuarantine ? "quarantine" : "good",
      min: Number((base - 1.2).toFixed(2)),
      max: Number((base + 1.2).toFixed(2)),
      samples: stepMinutes,
    });
  }

  const setpoints: SetpointBand[] = [
    { id: "hh", label: "HH", value: 55, kind: "HH" },
    { id: "h", label: "H", value: 50, kind: "H" },
    { id: "l", label: "L", value: 30, kind: "L" },
    { id: "ll", label: "LL", value: 25, kind: "LL" },
  ];

  const markers: EventMarker[] = [
    {
      id: "evt-alarm-1",
      ts: new Date(endTs - 2 * 24 * 60 * MINUTE_MS).toISOString(),
      event_name: "TAI4101 HH",
      severity: "alarm",
    },
    {
      id: "evt-warn-1",
      ts: new Date(endTs - 5 * 24 * 60 * MINUTE_MS).toISOString(),
      event_name: "TAI4101 H",
      severity: "warning",
    },
    {
      id: "evt-info-1",
      ts: new Date(endTs - 12 * 24 * 60 * MINUTE_MS).toISOString(),
      event_name: "sensor maintenance",
      severity: "info",
    },
  ];

  return {
    series,
    setpoints,
    markers,
    meta: {
      days,
      stepMinutes,
      pointCount: series.length,
      gapCount,
    },
  };
}

export function downsampleForDisplay(
  points: SeriesPointLike[],
  softCap: number,
): SeriesPointLike[] {
  if (points.length <= softCap) {
    return points;
  }
  const stride = Math.ceil(points.length / softCap);
  const out: SeriesPointLike[] = [];
  for (let i = 0; i < points.length; i += stride) {
    out.push(points[i]);
  }
  return out;
}
