import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  LAMP_QUALITIES,
  LAMP_SEVERITIES,
  LAMP_TEST_ID,
  type LampQuality,
  type LampSeverity,
} from "@/lib/ds/lamp-grammar-spec";

import { Lamp } from "./Lamp";

describe("Lamp", () => {
  it("should expose unique data-state for each severity×quality pair", () => {
    const states = new Set<string>();

    for (const severity of LAMP_SEVERITIES) {
      for (const quality of LAMP_QUALITIES) {
        const { unmount } = render(
          <Lamp severity={severity} lifecycle="active" quality={quality} />,
        );
        const el = screen.getByTestId(LAMP_TEST_ID);
        const state = el.getAttribute("data-state");
        expect(state).toBe(`${severity}:${quality}`);
        expect(states.has(state!)).toBe(false);
        states.add(state!);
        unmount();
      }
    }

    expect(states.size).toBe(LAMP_SEVERITIES.length * LAMP_QUALITIES.length);
  });

  it("should not treat quarantine as good class or overlay", () => {
    const { rerender, unmount } = render(
      <Lamp severity="norm" lifecycle="active" quality="good" />,
    );
    const good = screen.getByTestId(LAMP_TEST_ID);
    const goodState = good.getAttribute("data-state");
    expect(good.getAttribute("data-quality")).toBe("good");
    expect(good.className).not.toMatch(/quarantine/i);
    expect(good.querySelector("[data-overlay]")).toBeNull();
    expect(goodState).toBe("norm:good");

    rerender(
      <Lamp severity="norm" lifecycle="active" quality="quarantine" />,
    );
    const quarantine = screen.getByTestId(LAMP_TEST_ID);
    expect(quarantine.getAttribute("data-quality")).toBe("quarantine");
    expect(quarantine.className).toMatch(/quarantine/i);
    expect(quarantine.querySelector("[data-overlay='quarantine']")).not.toBeNull();
    expect(quarantine.getAttribute("data-state")).toBe("norm:quarantine");
    expect(quarantine.getAttribute("data-state")).not.toBe(goodState);
    unmount();
  });

  it("should set data-pulse on for active critical severities", () => {
    const { unmount } = render(
      <Lamp severity="alarm" lifecycle="active" quality="good" />,
    );
    const el = screen.getByTestId(LAMP_TEST_ID);
    expect(el.getAttribute("data-pulse")).toMatch(/^(on|static)$/);
    unmount();
  });

  it("should set data-pulse off when acked", () => {
    const { unmount } = render(
      <Lamp severity="alarm" lifecycle="acked" quality="good" />,
    );
    expect(screen.getByTestId(LAMP_TEST_ID).getAttribute("data-pulse")).toBe(
      "off",
    );
    unmount();
  });

  it("should expose severity lifecycle quality attrs", () => {
    const severity: LampSeverity = "warning-drift";
    const quality: LampQuality = "stale";
    const { unmount } = render(
      <Lamp
        severity={severity}
        lifecycle="cleared"
        quality={quality}
        size="lg"
        reconstructed
      />,
    );
    const el = screen.getByTestId(LAMP_TEST_ID);
    expect(el.getAttribute("data-severity")).toBe(severity);
    expect(el.getAttribute("data-lifecycle")).toBe("cleared");
    expect(el.getAttribute("data-quality")).toBe(quality);
    expect(el.getAttribute("data-reconstructed")).toBe("true");
    unmount();
  });
});
