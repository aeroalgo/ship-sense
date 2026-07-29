import uPlot from "uplot";
import type { AlignedData, Options } from "uplot";

import type {
  ChartMode,
  EventMarker,
  SeriesPointLike,
  SetpointBand,
} from "@/lib/trends/chart-lib-spec";
import { CHART_LIB } from "@/lib/trends/chart-lib-spec";
import {
  drawEventMarkers,
  drawSetpointBands,
  type OverlayDrawCtx,
} from "@/features/trends/spike/draw-overlays";
import {
  seriesToUplotAligned,
  type UplotAligned,
} from "@/features/trends/spike/gaps";

export type ChartTokenSnapshot = {
  seriesStroke: string;
  gridStroke: string;
  axisStroke: string;
  axisFont: string;
  background: string;
};

export const DEFAULT_CHART_TOKENS: ChartTokenSnapshot = {
  seriesStroke: "var(--accent, #6b9fd4)",
  gridStroke: "var(--border-subtle, #2a3340)",
  axisStroke: "var(--border-strong, #3d4654)",
  axisFont: "11px var(--font-mono, ui-monospace, monospace)",
  background: "var(--surface-0, #0f1419)",
};

export type UplotAdapterOpts = {
  series: SeriesPointLike[];
  setpoints: SetpointBand[];
  markers: EventMarker[];
  mode: ChartMode;
  onRangeChange: (from: string, to: string) => void;
  onMarkerClick?: (id: string) => void;
  tokens?: ChartTokenSnapshot;
  width?: number;
  height?: number;
};

export type UplotAdapterHandle = {
  destroy(): void;
  setSeries(s: SeriesPointLike[]): void;
  getAligned(): UplotAligned;
  lib: typeof CHART_LIB;
};

function toAlignedData(aligned: UplotAligned): AlignedData {
  return [aligned.xs, aligned.ys];
}

function buildOverlayCtx(u: uPlot): OverlayDrawCtx | null {
  const ctx = u.ctx;
  if (!ctx) {
    return null;
  }
  const left = u.bbox.left / devicePixelRatio;
  const top = u.bbox.top / devicePixelRatio;
  const width = u.bbox.width / devicePixelRatio;
  const height = u.bbox.height / devicePixelRatio;
  return {
    ctx,
    left,
    top,
    width,
    height,
    valToPosX: (ms) => u.valToPos(ms, "x"),
    valToPosY: (v) => u.valToPos(v, "y"),
  };
}

export function createUplotAdapter(
  el: HTMLElement,
  opts: UplotAdapterOpts,
): UplotAdapterHandle {
  const tokens = opts.tokens ?? DEFAULT_CHART_TOKENS;
  let aligned = seriesToUplotAligned(opts.series);
  let markerHits: Array<{ id: string; x: number; y: number; r: number }> = [];
  let setpoints = opts.setpoints;
  let markers = opts.markers;

  const width = opts.width ?? Math.max(el.clientWidth || 640, 320);
  const height = opts.height ?? Math.max(el.clientHeight || 280, 180);

  const plotOpts: Options = {
    width,
    height,
    cursor: {
      drag: { x: true, y: false },
    },
    scales: {
      x: { time: true },
    },
    axes: [
      {
        stroke: tokens.axisStroke,
        grid: { stroke: tokens.gridStroke, width: 1 },
        font: tokens.axisFont,
        ticks: { stroke: tokens.axisStroke },
      },
      {
        stroke: tokens.axisStroke,
        grid: { stroke: tokens.gridStroke, width: 1 },
        font: tokens.axisFont,
        ticks: { stroke: tokens.axisStroke },
        size: 56,
      },
    ],
    series: [
      {},
      {
        stroke: tokens.seriesStroke,
        width: 1.5,
        spanGaps: false,
        points: { show: false },
      },
    ],
    hooks: {
      draw: [
        (u) => {
          const overlay = buildOverlayCtx(u);
          if (!overlay) {
            markerHits = [];
            return;
          }
          drawSetpointBands(overlay, setpoints);
          markerHits = drawEventMarkers(overlay, markers);
        },
      ],
      setSelect: [
        (u) => {
          const sel = u.select;
          if (sel.width < 4) {
            return;
          }
          const left = u.posToVal(sel.left, "x");
          const right = u.posToVal(sel.left + sel.width, "x");
          const from = new Date(Math.min(left, right)).toISOString();
          const to = new Date(Math.max(left, right)).toISOString();
          opts.onRangeChange(from, to);
          u.setSelect({ left: 0, top: 0, width: 0, height: 0 }, false);
        },
      ],
    },
  };

  const plot = new uPlot(plotOpts, toAlignedData(aligned), el);

  const onClick = (ev: MouseEvent) => {
    if (!opts.onMarkerClick) {
      return;
    }
    const rect = plot.over.getBoundingClientRect();
    const x = ev.clientX - rect.left;
    const y = ev.clientY - rect.top;
    const hit = markerHits.find(
      (m) => (m.x - x) ** 2 + (m.y - y) ** 2 <= m.r ** 2,
    );
    if (hit) {
      opts.onMarkerClick(hit.id);
    }
  };
  plot.over.addEventListener("click", onClick);

  return {
    lib: CHART_LIB,
    getAligned: () => aligned,
    setSeries(s: SeriesPointLike[]) {
      aligned = seriesToUplotAligned(s);
      plot.setData(toAlignedData(aligned));
    },
    destroy() {
      plot.over.removeEventListener("click", onClick);
      plot.destroy();
    },
  };
}

export function countGaps(series: SeriesPointLike[]): number {
  return seriesToUplotAligned(series).gapIndexes.length;
}
