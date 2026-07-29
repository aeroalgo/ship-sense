import { describe, expect, it } from "vitest";

import {
  isCanvasSafeColor,
  resolveChartTokens,
  resolveCssColor,
} from "./resolveChartTokens";
import { DEFAULT_CHART_TOKENS } from "./uplotAdapter";

describe("resolveChartTokens", () => {
  it("resolves CSS var(--accent) to a concrete canvas-safe color", () => {
    const el = document.createElement("div");
    el.style.setProperty("--accent", "#6b9fd4");
    el.style.setProperty("--border-subtle", "#2a3340");
    el.style.setProperty("--border-strong", "#3d4654");
    el.style.setProperty("--surface-0", "#1a1d21");
    document.body.appendChild(el);

    const tokens = resolveChartTokens(el, DEFAULT_CHART_TOKENS);

    expect(tokens.seriesStroke).not.toMatch(/^var\(/);
    expect(isCanvasSafeColor(tokens.seriesStroke)).toBe(true);
    expect(tokens.seriesStroke.toLowerCase()).toBe("#6b9fd4");

    el.remove();
  });

  it("falls back when accent token missing (never black var)", () => {
    const el = document.createElement("div");
    document.body.appendChild(el);

    const color = resolveCssColor(el, "var(--accent, #6b9fd4)", "#6b9fd4");
    expect(isCanvasSafeColor(color)).toBe(true);
    expect(color).not.toMatch(/^var\(/);

    el.remove();
  });
});
