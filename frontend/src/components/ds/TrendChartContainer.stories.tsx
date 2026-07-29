import type { Meta, StoryObj } from "@storybook/react";

import { buildSpikeFixture } from "@/features/trends/spike/fixture-90d";

import { TrendChartContainer } from "./TrendChartContainer";

const fixture = buildSpikeFixture({ days: 7, stepMinutes: 30 });

const meta: Meta<typeof TrendChartContainer> = {
  title: "DS/TrendChartContainer",
  component: TrendChartContainer,
  args: {
    series: fixture.series,
    setpoints: fixture.setpoints,
    markers: fixture.markers,
    mode: "extended",
    quality: "good",
    tagLabel: "TAI4101",
    unit: "bar",
    resolutionLabel: "30 мин",
    onRangeChange: () => undefined,
  },
  parameters: {
    layout: "padded",
  },
};

export default meta;
type Story = StoryObj<typeof TrendChartContainer>;

export const ExtendedFixture: Story = {};

export const GapsDemo: Story = {
  args: {
    series: [
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
      {
        ts: "2026-07-26T10:04:00.000Z",
        value: 42,
        quality: "good",
        samples: 1,
      },
    ],
    setpoints: [
      { id: "hh", label: "HH", value: 55, kind: "HH" },
      { id: "h", label: "H", value: 50, kind: "H" },
    ],
    markers: [
      {
        id: "m1",
        ts: "2026-07-26T10:02:00.000Z",
        event_name: "TAI4101 H",
        severity: "warning",
      },
    ],
    mode: "quick",
    quality: "partial",
    tagLabel: "TAI4101",
    unit: "°C",
    resolutionLabel: "1 мин",
  },
};
