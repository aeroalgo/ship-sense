import type { SeriesPointLike } from "@/lib/trends/chart-lib-spec";
import { classifyPoint } from "@/lib/trends/chart-lib-spec";

export type UplotAligned = {
  xs: number[];
  ys: (number | null)[];
  gapIndexes: number[];
};

export function seriesToUplotAligned(points: SeriesPointLike[]): UplotAligned {
  const xs: number[] = [];
  const ys: (number | null)[] = [];
  const gapIndexes: number[] = [];

  for (let i = 0; i < points.length; i += 1) {
    const point = points[i];
    xs.push(Date.parse(point.ts));
    const kind = classifyPoint(point);
    if (kind === "line" || kind === "quarantine-dotted" || kind === "stale-edge") {
      ys.push(point.value);
    } else {
      ys.push(null);
      gapIndexes.push(i);
    }
  }

  return { xs, ys, gapIndexes };
}

export function assertNoZeroFilledGaps(
  points: SeriesPointLike[],
  ys: (number | null)[],
): void {
  for (let i = 0; i < points.length; i += 1) {
    const kind = classifyPoint(points[i]);
    if ((kind === "gap" || kind === "gap-bad-tick") && ys[i] === 0) {
      throw new Error(
        `gap at index ${i} must not be zero-filled (AC-8-05); got 0`,
      );
    }
    if ((kind === "gap" || kind === "gap-bad-tick") && ys[i] !== null) {
      throw new Error(
        `gap at index ${i} must be null in uPlot data; got ${String(ys[i])}`,
      );
    }
  }
}
