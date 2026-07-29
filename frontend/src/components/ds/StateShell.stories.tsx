import type { Meta, StoryObj } from "@storybook/react";

import { STATE_SHELL_VARIANTS, StateShell } from "./StateShell";

const meta: Meta<typeof StateShell> = {
  title: "DS/StateShell",
  component: StateShell,
  args: {
    variant: "loading",
  },
};

export default meta;
type Story = StoryObj<typeof StateShell>;

export const Loading: Story = { args: { variant: "loading" } };
export const Empty: Story = { args: { variant: "empty" } };
export const Error: Story = {
  args: { variant: "error", onRetry: () => undefined, message: "Сбой связи" },
};
export const Partial: Story = { args: { variant: "partial" } };
export const Stale: Story = { args: { variant: "stale" } };

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: "grid", gap: 12 }}>
      {STATE_SHELL_VARIANTS.map((variant) => (
        <StateShell
          key={variant}
          variant={variant}
          onRetry={variant === "error" ? () => undefined : undefined}
        />
      ))}
    </div>
  ),
};
