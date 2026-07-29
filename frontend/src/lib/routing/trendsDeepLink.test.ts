import { describe, expect, it } from "vitest";

import type { EventItem } from "@/lib/api/types";

import { QUICK_WINDOW_MS, trendsDeepLink } from "./trendsDeepLink";

const alarmEvent: EventItem = {
  id: "evt_00001234",
  ts: "2026-07-26T07:58:12.000Z",
  event_name: "alarm.HH",
  severity: "alarm",
  source: "aps",
  asset_id: "propulsion.geu.engine_1",
  params: {
    kks: "TAI4101",
    threshold: 80.0,
    value: 82.1,
  },
  quality: null,
};

describe("trendsDeepLink", () => {
  it("builds /trends quick window ±10min around event ts", () => {
    const href = trendsDeepLink(alarmEvent);
    expect(href).toBeTruthy();

    const url = new URL(href!, "http://localhost");
    expect(url.pathname).toBe("/trends");
    expect(url.searchParams.get("tag")).toBe("TAI4101");
    expect(url.searchParams.get("mode")).toBe("quick");

    const from = Date.parse(url.searchParams.get("from")!);
    const to = Date.parse(url.searchParams.get("to")!);
    const ts = Date.parse(alarmEvent.ts);
    expect(from).toBe(ts - QUICK_WINDOW_MS);
    expect(to).toBe(ts + QUICK_WINDOW_MS);
  });

  it("returns null when tag cannot be resolved", () => {
    expect(
      trendsDeepLink({
        ...alarmEvent,
        params: { threshold: 1 },
      }),
    ).toBeNull();
  });
});
