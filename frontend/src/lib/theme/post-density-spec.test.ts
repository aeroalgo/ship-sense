import { describe, expect, it } from "vitest";

import {
  CANONICAL_TYPE_SCALE_PX,
  FONT_CRITICAL_FLOOR_PX,
  TOUCH_MIN_FLOOR_PX,
  assertComputedFloorsMatchCanon,
  assertMeetsDensityFloor,
  criticalFontPx,
  criticalHeightMm,
  touchMinPx,
} from "./post-density-spec";

describe("post-density-spec (CR-UI-05)", () => {
  it("computes 1/200 critical height at 2.5 m", () => {
    expect(criticalHeightMm()).toBe(12.5);
    expect(criticalFontPx()).toBe(FONT_CRITICAL_FLOOR_PX);
    expect(criticalFontPx()).toBe(48);
  });

  it("computes touch ≥15 mm in CSS px", () => {
    expect(touchMinPx()).toBe(TOUCH_MIN_FLOOR_PX);
    expect(touchMinPx()).toBe(57);
  });

  it("canonical scale meets floor", () => {
    expect(() => assertMeetsDensityFloor(CANONICAL_TYPE_SCALE_PX)).not.toThrow();
    expect(() => assertComputedFloorsMatchCanon()).not.toThrow();
  });

  it("rejects scale below critical floor", () => {
    expect(() =>
      assertMeetsDensityFloor({
        ...CANONICAL_TYPE_SCALE_PX,
        critical: 40,
      }),
    ).toThrow(/G-DS0-2-02/);
  });
});
