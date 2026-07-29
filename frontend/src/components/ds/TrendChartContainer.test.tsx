import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TREND_CHART_TEST_ID } from "@/lib/trends/chart-lib-spec";
import { buildSpikeFixture } from "@/features/trends/spike/fixture-90d";
import {
  assertNoZeroFilledGaps,
  seriesToUplotAligned,
} from "@/features/trends/spike/gaps";

import { TrendChartContainer } from "./TrendChartContainer";

describe("TrendChartContainer", () => {
  it("should break the line on null bucket without zero-fill (AC-8-05)", () => {
    const series = [
      {
        ts: "2026-07-26T10:00:00.000Z",
        value: 40,
        quality: "good",
        samples: 1,
      },
      {
        ts: "2026-07-26T10:01:00.000Z",
        value: null,
        quality: "good",
        samples: 0,
      },
      {
        ts: "2026-07-26T10:02:00.000Z",
        value: 41,
        quality: "good",
        samples: 1,
      },
      {
        ts: "2026-07-26T10:03:00.000Z",
        value: null,
        quality: "bad",
        samples: 0,
      },
    ];

    const aligned = seriesToUplotAligned(series);
    expect(aligned.ys[1]).toBeNull();
    expect(aligned.ys[3]).toBeNull();
    expect(aligned.ys).not.toContain(0);
    assertNoZeroFilledGaps(series, aligned.ys);

    render(
      <TrendChartContainer
        series={series}
        setpoints={[]}
        markers={[]}
        mode="quick"
        quality="partial"
        tagLabel="TAI4101"
        unit="°C"
        onRangeChange={vi.fn()}
      />,
    );

    const root = screen.getByTestId(TREND_CHART_TEST_ID);
    expect(root).toBeInTheDocument();
    expect(root.getAttribute("data-gap-count")).toBe("2");
    expect(root.getAttribute("data-chart-lib")).toBe("uplot");
  });

  it("should expose setpoint render count (AC-8-01 partial)", () => {
    const setpoints = [
      { id: "hh", label: "HH", value: 55, kind: "HH" as const },
      { id: "h", label: "H", value: 50, kind: "H" as const },
      { id: "l", label: "L", value: 30, kind: "L" as const },
    ];

    render(
      <TrendChartContainer
        series={[
          {
            ts: "2026-07-26T10:00:00.000Z",
            value: 42,
            quality: "good",
            samples: 1,
          },
        ]}
        setpoints={setpoints}
        markers={[]}
        mode="extended"
        quality="good"
        resolutionLabel="1 мин"
        onRangeChange={vi.fn()}
      />,
    );

    const root = screen.getByTestId(TREND_CHART_TEST_ID);
    expect(root.getAttribute("data-setpoint-count")).toBe("3");
    expect(screen.getByTestId("trend-chart-setpoints").children).toHaveLength(
      3,
    );
  });

  it("should mount integration fixture §9.4 #5 with gaps and overlays", () => {
    const fixture = buildSpikeFixture({ days: 7, stepMinutes: 30 });
    const aligned = seriesToUplotAligned(fixture.series);
    assertNoZeroFilledGaps(fixture.series, aligned.ys);

    render(
      <TrendChartContainer
        series={fixture.series}
        setpoints={fixture.setpoints}
        markers={fixture.markers}
        mode="extended"
        quality="good"
        tagLabel="TAI4101"
        unit="bar"
        resolutionLabel="30 мин"
        onRangeChange={vi.fn()}
      />,
    );

    const root = screen.getByTestId(TREND_CHART_TEST_ID);
    expect(root.getAttribute("data-gap-count")).toBe(
      String(aligned.gapIndexes.length),
    );
    expect(root.getAttribute("data-setpoint-count")).toBe(
      String(fixture.setpoints.length),
    );
    expect(root.getAttribute("data-marker-count")).toBe(
      String(fixture.markers.length),
    );
    expect(root.getAttribute("aria-label")).toMatch(/TAI4101/);
  });
});
