import { cleanup, renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { computeStale, useStaleGate } from "./useStaleGate";

describe("computeStale", () => {
  it("returns true when forceStale", () => {
    expect(
      computeStale({
        lastFreshTs: "2026-07-26T10:00:00.000Z",
        nowMs: Date.parse("2026-07-26T10:00:01.000Z"),
        thresholdSec: 10,
        forceStale: true,
      }),
    ).toBe(true);
  });

  it("returns true when age exceeds threshold", () => {
    expect(
      computeStale({
        lastFreshTs: "2026-07-26T10:00:00.000Z",
        nowMs: Date.parse("2026-07-26T10:00:11.000Z"),
        thresholdSec: 10,
        forceStale: false,
      }),
    ).toBe(true);
  });

  it("returns false when age is within threshold", () => {
    expect(
      computeStale({
        lastFreshTs: "2026-07-26T10:00:00.000Z",
        nowMs: Date.parse("2026-07-26T10:00:09.000Z"),
        thresholdSec: 10,
        forceStale: false,
      }),
    ).toBe(false);
  });
});

describe("useStaleGate", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_STALE_THRESHOLD_SEC = "10";
    document.body.removeAttribute("data-stale");
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-26T10:00:15.000Z"));
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    document.body.removeAttribute("data-stale");
  });

  it("sets body data-stale=true when stale", () => {
    const { result } = renderHook(() =>
      useStaleGate({
        lastFreshTs: "2026-07-26T10:00:00.000Z",
        forceStale: false,
      }),
    );

    expect(result.current.stale).toBe(true);
    expect(document.body.getAttribute("data-stale")).toBe("true");
  });

  it("clears body data-stale when fresh", () => {
    document.body.setAttribute("data-stale", "true");
    vi.setSystemTime(new Date("2026-07-26T10:00:05.000Z"));

    const { result } = renderHook(() =>
      useStaleGate({
        lastFreshTs: "2026-07-26T10:00:00.000Z",
        forceStale: false,
      }),
    );

    expect(result.current.stale).toBe(false);
    expect(document.body.getAttribute("data-stale")).toBe("false");
  });

  it("throws when NEXT_PUBLIC_STALE_THRESHOLD_SEC is missing", () => {
    delete process.env.NEXT_PUBLIC_STALE_THRESHOLD_SEC;
    expect(() =>
      renderHook(() =>
        useStaleGate({ lastFreshTs: "2026-07-26T10:00:00.000Z" }),
      ),
    ).toThrow(/NEXT_PUBLIC_STALE_THRESHOLD_SEC/);
  });
});
