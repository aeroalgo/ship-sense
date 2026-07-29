import type { EventMarker, SetpointBand } from "@/lib/trends/chart-lib-spec";
import {
  markerSeverityShape,
  setpointStrokeToken,
} from "@/lib/trends/chart-lib-spec";

export type OverlayDrawCtx = {
  ctx: CanvasRenderingContext2D;
  /** uPlot bbox: plot left/top/width/height in CSS px */
  left: number;
  top: number;
  width: number;
  height: number;
  /** map data x (ms) → canvas x */
  valToPosX: (ms: number) => number;
  /** map data y → canvas y */
  valToPosY: (v: number) => number;
};

export function drawSetpointBands(
  overlay: OverlayDrawCtx,
  bands: SetpointBand[],
): void {
  const { ctx, left, width } = overlay;
  for (const band of bands) {
    const y = overlay.valToPosY(band.value);
    ctx.save();
    ctx.strokeStyle = setpointStrokeToken(band.kind);
    ctx.globalAlpha = 0.85;
    ctx.lineWidth = 1;
    ctx.setLineDash(band.kind === "HH" || band.kind === "LL" ? [] : [6, 4]);
    ctx.beginPath();
    ctx.moveTo(left, y);
    ctx.lineTo(left + width, y);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = setpointStrokeToken(band.kind);
    ctx.font = "11px var(--font-mono, ui-monospace, monospace)";
    ctx.textAlign = "right";
    ctx.fillText(band.label, left + width - 4, y - 4);
    ctx.restore();
  }
}

export function drawEventMarkers(
  overlay: OverlayDrawCtx,
  markers: EventMarker[],
  hitRadius = 22,
): Array<{ id: string; x: number; y: number; r: number }> {
  const hits: Array<{ id: string; x: number; y: number; r: number }> = [];
  const { ctx, top, height } = overlay;
  const baseline = top + height;

  for (const marker of markers) {
    const x = overlay.valToPosX(Date.parse(marker.ts));
    const shape = markerSeverityShape(marker.severity);
    const size = 7;
    ctx.save();
    ctx.fillStyle =
      marker.severity === "critical" || marker.severity === "alarm"
        ? "var(--alarm-critical-fg, #ff4d4f)"
        : marker.severity === "warning"
          ? "var(--alarm-warning-fg, #faad14)"
          : "var(--alarm-info-fg, #69b1ff)";
    ctx.beginPath();
    if (shape === "diamond") {
      ctx.moveTo(x, baseline - size * 2);
      ctx.lineTo(x + size, baseline - size);
      ctx.lineTo(x, baseline);
      ctx.lineTo(x - size, baseline - size);
      ctx.closePath();
    } else if (shape === "triangle") {
      ctx.moveTo(x, baseline - size * 2);
      ctx.lineTo(x + size, baseline);
      ctx.lineTo(x - size, baseline);
      ctx.closePath();
    } else {
      ctx.arc(x, baseline - size, size * 0.7, 0, Math.PI * 2);
    }
    ctx.fill();
    ctx.restore();
    hits.push({ id: marker.id, x, y: baseline - size, r: hitRadius });
  }

  return hits;
}
