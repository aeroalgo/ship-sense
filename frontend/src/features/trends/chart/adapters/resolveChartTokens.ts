import {
  DEFAULT_CHART_TOKENS,
  type ChartTokenSnapshot,
} from "./uplotAdapter";

const SERIES_FALLBACK = "#6b9fd4";
const GRID_FALLBACK = "#2a3340";
const AXIS_FALLBACK = "#3d4654";

function extractCssVar(value: string): string | null {
  const match = value.match(/var\(\s*(--[\w-]+)/);
  return match?.[1] ?? null;
}

export function resolveCssColor(
  el: HTMLElement,
  tokenValue: string,
  fallback: string,
): string {
  const trimmed = tokenValue.trim();
  if (!trimmed.startsWith("var(")) {
    return trimmed || fallback;
  }
  const prop = extractCssVar(trimmed);
  if (!prop) {
    return fallback;
  }
  const computed = getComputedStyle(el).getPropertyValue(prop).trim();
  if (!computed) {
    return fallback;
  }
  if (computed.startsWith("var(")) {
    return resolveCssColor(el, computed, fallback);
  }
  return computed;
}

export function resolveChartTokens(
  el: HTMLElement,
  tokens: ChartTokenSnapshot = DEFAULT_CHART_TOKENS,
): ChartTokenSnapshot {
  return {
    seriesStroke: resolveCssColor(el, tokens.seriesStroke, SERIES_FALLBACK),
    gridStroke: resolveCssColor(el, tokens.gridStroke, GRID_FALLBACK),
    axisStroke: resolveCssColor(el, tokens.axisStroke, AXIS_FALLBACK),
    axisFont: tokens.axisFont,
    background: resolveCssColor(
      el,
      tokens.background,
      getComputedStyle(el).backgroundColor || "#0f1419",
    ),
  };
}

export function isCanvasSafeColor(color: string): boolean {
  const c = color.trim().toLowerCase();
  if (!c || c.startsWith("var(")) return false;
  if (c === "#000" || c === "#000000" || c === "black" || c === "rgb(0, 0, 0)") {
    return false;
  }
  return true;
}
