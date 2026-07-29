import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  HANDOFF_ACTIVE_ALARMS,
  HANDOFF_ACTIVE_NOW,
} from "@/lib/routing/handoff";

import {
  HANDOFF_BUTTON_TEST_ID,
  HandoffButton,
} from "./HandoffButton";

afterEach(() => {
  cleanup();
});

describe("HandoffButton", () => {
  it("links to active alarms journal and overview active-now", () => {
    render(<HandoffButton />);

    const root = screen.getByTestId(HANDOFF_BUTTON_TEST_ID);
    expect(root).toBeInTheDocument();

    const alarms = screen.getByRole("link", {
      name: HANDOFF_ACTIVE_ALARMS.label,
    });
    expect(alarms).toHaveAttribute("href", HANDOFF_ACTIVE_ALARMS.href);

    const activeNow = screen.getByTestId(HANDOFF_ACTIVE_NOW.testId);
    expect(activeNow).toHaveAttribute("href", HANDOFF_ACTIVE_NOW.href);
    expect(activeNow).toHaveTextContent(HANDOFF_ACTIVE_NOW.label);
  });

  it("allows active-now navigation without session (anonymous)", () => {
    render(<HandoffButton />);

    const activeNow = screen.getByTestId("handoff-active-now");
    expect(activeNow.tagName).toBe("A");
    expect(activeNow).toHaveAttribute("href", "/overview");
    expect(activeNow).not.toHaveAttribute("aria-disabled", "true");
  });
});
