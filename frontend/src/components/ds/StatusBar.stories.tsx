import type { Meta, StoryObj } from "@storybook/react";

import { StatusBar } from "./StatusBar";
import { SessionChip } from "./SessionChip";
import { ThemeSwitcher } from "./ThemeSwitcher";

const meta: Meta<typeof StatusBar> = {
  title: "DS/StatusBar",
  component: StatusBar,
};

export default meta;
type Story = StoryObj<typeof StatusBar>;

export const Loading: Story = {
  args: {
    alarms: [],
    children: <span style={{ color: "var(--text-muted)" }}>Загрузка…</span>,
  },
};

export const Empty: Story = {
  args: { alarms: [] },
};

export const Error: Story = {
  args: {
    alarms: [
      {
        id: "1",
        label: "Сбой канала АПС",
        severity: "protection-shutdown",
      },
    ],
  },
};

export const Partial: Story = {
  args: {
    alarms: [
      {
        id: "1",
        label: "ГЭУ1 HH",
        severity: "alarm",
        quality: "quarantine",
      },
      {
        id: "2",
        label: "Дрейф TAI",
        severity: "warning-drift",
        quality: "uncertain",
      },
    ],
    children: (
      <>
        <ThemeSwitcher theme="day" onChange={() => undefined} />
        <SessionChip name="Иванов" rank="вахтенный" />
      </>
    ),
  },
};

export const Stale: Story = {
  args: {
    alarms: [
      {
        id: "1",
        label: "Последняя тревога",
        severity: "alarm",
        quality: "stale",
        lifecycle: "acked",
      },
    ],
    compact: true,
  },
};
