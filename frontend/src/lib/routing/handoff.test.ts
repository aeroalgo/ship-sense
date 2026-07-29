import { describe, expect, it } from "vitest";

import {
  HANDOFF_ACTIVE_ALARMS,
  HANDOFF_ACTIVE_NOW,
  handoffActiveAlarmsHref,
  handoffActiveNowHref,
  isActiveFlag,
  isSessionAuditFlag,
  parseHandoffJournalFlags,
  withHandoffJournalFlags,
} from "./handoff";

describe("handoff routing", () => {
  it("targets overview for active-now (product: overview first)", () => {
    expect(handoffActiveNowHref()).toBe("/overview");
    expect(HANDOFF_ACTIVE_NOW.href).toBe("/overview");
    expect(HANDOFF_ACTIVE_NOW.testId).toBe("handoff-active-now");
  });

  it("targets journal alarms with active=1 for primary CTA", () => {
    expect(handoffActiveAlarmsHref()).toBe(
      "/journal?severity=alarm&active=1",
    );
    expect(HANDOFF_ACTIVE_ALARMS.href).toBe(
      "/journal?severity=alarm&active=1",
    );

    const url = new URL(handoffActiveAlarmsHref(), "http://localhost");
    expect(url.pathname).toBe("/journal");
    expect(url.searchParams.get("severity")).toBe("alarm");
    expect(url.searchParams.get("active")).toBe("1");
  });

  it("parses and preserves active + session audit flags", () => {
    const flags = parseHandoffJournalFlags(
      new URLSearchParams("severity=alarm&active=1&session=1"),
    );
    expect(flags.active).toBe(true);
    expect(flags.sessionAudit).toBe(true);
    expect(isActiveFlag(new URLSearchParams("active=1"))).toBe(true);
    expect(isSessionAuditFlag(new URLSearchParams("session=1"))).toBe(true);

    const next = withHandoffJournalFlags(new URLSearchParams("severity=alarm"), {
      active: true,
      sessionAudit: false,
    });
    expect(next.get("active")).toBe("1");
    expect(next.get("session")).toBeNull();
    expect(next.get("severity")).toBe("alarm");
  });
});
