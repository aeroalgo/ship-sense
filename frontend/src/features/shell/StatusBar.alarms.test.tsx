import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { StatusBar } from "@/components/ds/StatusBar";

describe("StatusBar alarm click", () => {
  afterEach(() => {
    cleanup();
  });

  it("calls onAlarmClick with alarm id", () => {
    const onAlarmClick = vi.fn();
    render(
      <StatusBar
        alarms={[
          {
            id: "evt_alarm_1",
            label: "ТАІ4101 HH",
            severity: "alarm",
          },
        ]}
        onAlarmClick={onAlarmClick}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /ТАІ4101 HH/i }));

    expect(onAlarmClick).toHaveBeenCalledTimes(1);
    expect(onAlarmClick.mock.calls[0][0].id).toBe("evt_alarm_1");
  });
});
