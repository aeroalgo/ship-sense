export const HANDOFF_ACTIVE_NOW = {
  label: "Что активно сейчас",
  href: "/overview",
  testId: "handoff-active-now",
} as const;

export const HANDOFF_ACTIVE_ALARMS = {
  label: "К активным тревогам",
  href: "/journal?severity=alarm&active=1",
  testId: "handoff-active-alarms",
} as const;

export const SESSION_AUDIT_EVENT_NAMES = [
  "session_started",
  "session_ended",
] as const;

export type HandoffJournalFlags = {
  active: boolean;
  sessionAudit: boolean;
};

export function handoffActiveNowHref(): string {
  return HANDOFF_ACTIVE_NOW.href;
}

export function handoffActiveAlarmsHref(): string {
  return HANDOFF_ACTIVE_ALARMS.href;
}

export function isActiveFlag(params: URLSearchParams): boolean {
  return params.get("active") === "1";
}

export function isSessionAuditFlag(params: URLSearchParams): boolean {
  return params.get("session") === "1";
}

export function parseHandoffJournalFlags(
  params: URLSearchParams,
): HandoffJournalFlags {
  return {
    active: isActiveFlag(params),
    sessionAudit: isSessionAuditFlag(params),
  };
}

export function withHandoffJournalFlags(
  params: URLSearchParams,
  flags: HandoffJournalFlags,
): URLSearchParams {
  const next = new URLSearchParams(params);
  if (flags.active) {
    next.set("active", "1");
  } else {
    next.delete("active");
  }
  if (flags.sessionAudit) {
    next.set("session", "1");
    if (!next.get("source")) {
      next.set("source", "edge");
    }
  } else {
    next.delete("session");
  }
  return next;
}

export function isSessionAuditEventName(eventName: string): boolean {
  return (SESSION_AUDIT_EVENT_NAMES as readonly string[]).includes(eventName);
}
