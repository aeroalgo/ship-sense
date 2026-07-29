import type { Meta, StoryObj } from "@storybook/react";

import { LAMP_QUALITIES, LAMP_SEVERITIES } from "@/lib/ds/lamp-grammar-spec";

import { Lamp } from "./Lamp";

const meta: Meta<typeof Lamp> = {
  title: "DS/Lamp",
  component: Lamp,
  args: {
    severity: "alarm",
    lifecycle: "active",
    quality: "good",
    size: "lg",
  },
};

export default meta;
type Story = StoryObj<typeof Lamp>;

export const Default: Story = {};

export const Lifecycle: Story = {
  render: () => (
    <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
      <Lamp severity="alarm" lifecycle="active" quality="good" size="xl" />
      <Lamp severity="alarm" lifecycle="acked" quality="good" size="xl" />
      <Lamp severity="alarm" lifecycle="cleared" quality="good" size="xl" />
    </div>
  ),
};

export const Matrix: Story = {
  render: () => (
    <table style={{ borderCollapse: "collapse", color: "var(--text-primary)" }}>
      <thead>
        <tr>
          <th />
          {LAMP_QUALITIES.map((q) => (
            <th key={q} style={{ padding: 8, fontWeight: 400 }}>
              {q}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {LAMP_SEVERITIES.map((severity) => (
          <tr key={severity}>
            <td style={{ padding: 8 }}>{severity}</td>
            {LAMP_QUALITIES.map((quality) => (
              <td key={quality} style={{ padding: 8, textAlign: "center" }}>
                <Lamp
                  severity={severity}
                  lifecycle="active"
                  quality={quality}
                  size="md"
                />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  ),
};

export const QuarantineVsGood: Story = {
  render: () => (
    <div style={{ display: "flex", gap: 24 }}>
      <Lamp severity="norm" lifecycle="active" quality="good" size="xl" />
      <Lamp severity="norm" lifecycle="active" quality="quarantine" size="xl" />
    </div>
  ),
};
