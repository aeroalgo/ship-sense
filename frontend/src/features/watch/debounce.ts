import {
  DATA_QUALITY_PANEL_TEST_ID,
  DEBOUNCE_GROUP_TEST_ID,
  DEBOUNCE_MIN_COUNT,
  DEBOUNCE_WINDOW_MS,
  DRIFTS_STUB_COPY,
  HANDOFF_BANNER_COPY,
  HANDOFF_BANNER_MS,
  HANDOFF_PRIMARY,
  HANDOFF_SECONDARY,
  SECTION_ORDER,
  SECTION_TITLES,
  WATCH_SECTION_TEST_ID,
  WATCH_VERDICT_TEST_ID,
  buildVerdict,
  collapseDebounceGroups,
  debounceGroupKey,
  formatDebounceLabel,
  isProtectionEvent,
  resolveVerdict,
  type DebounceEventLike,
  type DebounceGroup,
  type VerdictInput,
  type VerdictResult,
  type WatchSectionId,
  type WatchVerdictTone,
} from "@/lib/watch/watch-compression-spec";

export {
  DATA_QUALITY_PANEL_TEST_ID,
  DEBOUNCE_GROUP_TEST_ID,
  DEBOUNCE_MIN_COUNT,
  DEBOUNCE_WINDOW_MS,
  DRIFTS_STUB_COPY,
  HANDOFF_BANNER_COPY,
  HANDOFF_BANNER_MS,
  HANDOFF_PRIMARY,
  HANDOFF_SECONDARY,
  SECTION_ORDER,
  SECTION_TITLES,
  WATCH_SECTION_TEST_ID,
  WATCH_VERDICT_TEST_ID,
  buildVerdict,
  collapseDebounceGroups,
  debounceGroupKey,
  formatDebounceLabel,
  isProtectionEvent,
  resolveVerdict,
};
export type {
  DebounceEventLike,
  DebounceGroup,
  VerdictInput,
  VerdictResult,
  WatchSectionId,
  WatchVerdictTone,
};

export function verdictCountConflict(
  serverVerdict: string | null | undefined,
  input: VerdictInput,
): boolean {
  const s = serverVerdict?.trim() ?? "";
  if (!s) return false;
  if (input.protections_count > 0 && /защит(?:ы)?\s*:?\s*0\b/i.test(s)) {
    return true;
  }
  if (
    input.alarms_count === 0 &&
    input.protections_count === 0 &&
    /(тревог|защит)/i.test(s) &&
    !/не зафиксировано/i.test(s)
  ) {
    return true;
  }
  return false;
}

export function formatWatchTime(ts: string): string {
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function defaultWatchPeriod(now = new Date()): {
  from: string;
  to: string;
} {
  const to = now.toISOString();
  const from = new Date(now.getTime() - 8 * 60 * 60 * 1000).toISOString();
  return { from, to };
}

export function splitWatchEvents(events: readonly DebounceEventLike[]): {
  protections: DebounceEventLike[];
  alarms: DebounceEventLike[];
} {
  const protections: DebounceEventLike[] = [];
  const alarms: DebounceEventLike[] = [];
  for (const event of events) {
    if (isProtectionEvent(event)) {
      protections.push(event);
      continue;
    }
    if (event.severity === "alarm" || event.severity === "warning") {
      alarms.push(event);
    }
  }
  protections.sort(
    (a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime(),
  );
  return { protections, alarms };
}

export function eventsFromHighlights(
  highlights: unknown[],
): DebounceEventLike[] | null {
  if (!Array.isArray(highlights) || highlights.length === 0) {
    return null;
  }
  const out: DebounceEventLike[] = [];
  for (const item of highlights) {
    if (!item || typeof item !== "object") return null;
    const row = item as Record<string, unknown>;
    if (typeof row.id !== "string" || typeof row.ts !== "string") return null;
    if (typeof row.event_name !== "string") return null;
    out.push({
      id: row.id,
      ts: row.ts,
      event_name: row.event_name,
      asset_id:
        typeof row.asset_id === "string" || row.asset_id === null
          ? (row.asset_id as string | null)
          : null,
      severity: typeof row.severity === "string" ? row.severity : null,
      source: typeof row.source === "string" ? row.source : null,
      params:
        row.params && typeof row.params === "object"
          ? (row.params as Record<string, unknown>)
          : undefined,
    });
  }
  return out;
}
