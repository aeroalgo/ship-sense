import { describe, expect, it } from "vitest";

import {
  DEBOUNCE_MIN_COUNT,
  DEBOUNCE_WINDOW_MS,
  buildVerdict,
  collapseDebounceGroups,
  isProtectionEvent,
  resolveVerdict,
  splitWatchEvents,
  type DebounceEventLike,
} from "./debounce";

function evt(
  partial: Partial<DebounceEventLike> &
    Pick<DebounceEventLike, "id" | "ts" | "event_name">,
): DebounceEventLike {
  return {
    asset_id: "propulsion.geu.engine_1",
    severity: "alarm",
    ...partial,
  };
}

describe("watch debounce", () => {
  it("collapses same key when count >= DEBOUNCE_MIN_COUNT within window", () => {
    const base = Date.parse("2026-07-26T08:00:00Z");
    const events = [0, 1, 2].map((i) =>
      evt({
        id: `a${i}`,
        ts: new Date(base + i * 60_000).toISOString(),
        event_name: "alarm.HH",
      }),
    );

    const groups = collapseDebounceGroups(events);
    expect(DEBOUNCE_MIN_COUNT).toBe(3);
    expect(DEBOUNCE_WINDOW_MS).toBe(300_000);
    expect(groups).toHaveLength(1);
    expect(groups[0].count).toBe(3);
    expect(groups[0].collapsed).toBe(true);
  });

  it("does not collapse when count < min", () => {
    const base = Date.parse("2026-07-26T08:00:00Z");
    const events = [0, 1].map((i) =>
      evt({
        id: `b${i}`,
        ts: new Date(base + i * 60_000).toISOString(),
        event_name: "alarm.HH",
      }),
    );
    const groups = collapseDebounceGroups(events);
    expect(groups).toHaveLength(1);
    expect(groups[0].collapsed).toBe(false);
    expect(groups[0].count).toBe(2);
  });

  it("splits cluster when gap > window", () => {
    const base = Date.parse("2026-07-26T08:00:00Z");
    const events = [
      evt({ id: "c0", ts: new Date(base).toISOString(), event_name: "alarm.HH" }),
      evt({
        id: "c1",
        ts: new Date(base + 60_000).toISOString(),
        event_name: "alarm.HH",
      }),
      evt({
        id: "c2",
        ts: new Date(base + 120_000).toISOString(),
        event_name: "alarm.HH",
      }),
      evt({
        id: "c3",
        ts: new Date(base + DEBOUNCE_WINDOW_MS + 1).toISOString(),
        event_name: "alarm.HH",
      }),
      evt({
        id: "c4",
        ts: new Date(base + DEBOUNCE_WINDOW_MS + 60_001).toISOString(),
        event_name: "alarm.HH",
      }),
      evt({
        id: "c5",
        ts: new Date(base + DEBOUNCE_WINDOW_MS + 120_001).toISOString(),
        event_name: "alarm.HH",
      }),
    ];
    const groups = collapseDebounceGroups(events);
    expect(groups).toHaveLength(2);
    expect(groups.every((g) => g.collapsed)).toBe(true);
  });

  it("never treats protections as collapsible alarm groups", () => {
    const trip = evt({
      id: "p1",
      ts: "2026-07-26T08:10:00Z",
      event_name: "GEU1 overspeed trip",
      severity: "alarm",
      params: { kind: "protection" },
    });
    expect(isProtectionEvent(trip)).toBe(true);

    const { protections, alarms } = splitWatchEvents([
      trip,
      evt({
        id: "a1",
        ts: "2026-07-26T08:11:00Z",
        event_name: "alarm.HH",
      }),
      evt({
        id: "a2",
        ts: "2026-07-26T08:12:00Z",
        event_name: "alarm.HH",
      }),
      evt({
        id: "a3",
        ts: "2026-07-26T08:13:00Z",
        event_name: "alarm.HH",
      }),
    ]);

    expect(protections).toHaveLength(1);
    expect(protections[0].id).toBe("p1");
    const alarmGroups = collapseDebounceGroups(alarms);
    expect(alarmGroups).toHaveLength(1);
    expect(alarmGroups[0].collapsed).toBe(true);
    expect(alarmGroups[0].member_ids).not.toContain("p1");
  });

  it("buildVerdict / resolveVerdict when alarms exist", () => {
    const input = {
      alarms_count: 3,
      protections_count: 0,
      system_labels: ["ГЭУ1"],
    };
    const client = buildVerdict(input);
    expect(client.tone).toBe("attention");
    expect(client.text).toMatch(/тревог/i);

    const resolved = resolveVerdict({
      serverVerdict: "Были тревоги по ГЭУ1; защит: 0",
      input,
    });
    expect(resolved.text).toBe("Были тревоги по ГЭУ1; защит: 0");
    expect(resolved.tone).toBe("attention");
  });
});
