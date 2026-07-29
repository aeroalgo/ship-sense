import type { EventFiltersValue } from "@/components/ds/EventFilters";
import type { EventsQuery } from "@/lib/api/types";
import {
  isSessionAuditEventName,
  parseHandoffJournalFlags,
  withHandoffJournalFlags,
} from "@/lib/routing/handoff";

export type JournalFiltersValue = EventFiltersValue & {
  active?: boolean;
  sessionAudit?: boolean;
};

export function filtersFromSearchParams(
  params: URLSearchParams,
): JournalFiltersValue {
  const severity = params.get("severity");
  const flags = parseHandoffJournalFlags(params);
  const source = params.get("source") ?? undefined;
  return {
    eventName: params.get("event_name") ?? undefined,
    severity:
      severity === "info" ||
      severity === "warning" ||
      severity === "alarm"
        ? severity
        : severity === ""
          ? ""
          : undefined,
    assetId: params.get("asset_id") ?? undefined,
    source,
    from: isoToDatetimeLocal(params.get("from")),
    to: isoToDatetimeLocal(params.get("to")),
    active: flags.active || undefined,
    sessionAudit: flags.sessionAudit || undefined,
  };
}

export function searchParamsFromFilters(
  filters: JournalFiltersValue,
): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.eventName) params.set("event_name", filters.eventName);
  if (filters.severity) params.set("severity", filters.severity);
  if (filters.assetId) params.set("asset_id", filters.assetId);
  if (filters.source) params.set("source", filters.source);
  const fromIso = datetimeLocalToIso(filters.from);
  const toIso = datetimeLocalToIso(filters.to);
  if (fromIso) params.set("from", fromIso);
  if (toIso) params.set("to", toIso);
  return withHandoffJournalFlags(params, {
    active: Boolean(filters.active),
    sessionAudit: Boolean(filters.sessionAudit),
  });
}

export function filtersToEventsQuery(
  filters: JournalFiltersValue,
): EventsQuery {
  const query: EventsQuery = { limit: 50 };
  if (filters.eventName) query.event_name = filters.eventName;
  if (filters.severity) query.severity = filters.severity;
  if (filters.assetId) query.asset_id = filters.assetId;
  if (filters.source) query.source = filters.source;
  if (filters.sessionAudit && !filters.source) {
    query.source = "edge";
  }
  const fromIso = datetimeLocalToIso(filters.from);
  const toIso = datetimeLocalToIso(filters.to);
  if (fromIso) query.from = fromIso;
  if (toIso) query.to = toIso;
  return query;
}

export function eventMatchesFilters(
  event: {
    event_name: string;
    severity: string | null;
    asset_id?: string | null;
    source: string;
    ts: string;
  },
  filters: JournalFiltersValue,
): boolean {
  if (filters.sessionAudit && !isSessionAuditEventName(event.event_name)) {
    return false;
  }
  if (filters.eventName && event.event_name !== filters.eventName) {
    return false;
  }
  if (filters.severity && event.severity !== filters.severity) {
    return false;
  }
  if (filters.assetId && event.asset_id !== filters.assetId) {
    return false;
  }
  if (filters.source && event.source !== filters.source) {
    return false;
  }
  const fromIso = datetimeLocalToIso(filters.from);
  const toIso = datetimeLocalToIso(filters.to);
  if (fromIso && event.ts < fromIso) return false;
  if (toIso && event.ts > toIso) return false;
  return true;
}

function isoToDatetimeLocal(value: string | null): string | undefined {
  if (!value) return undefined;
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) return value;
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) return value.slice(0, 16);
  return new Date(parsed).toISOString().slice(0, 16);
}

function datetimeLocalToIso(value: string | undefined): string | undefined {
  if (!value) return undefined;
  if (value.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(value)) {
    return new Date(value).toISOString();
  }
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) {
    return `${value}:00.000Z`;
  }
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(value)) {
    return value.endsWith("Z") ? value : `${value}Z`;
  }
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) return undefined;
  return new Date(parsed).toISOString();
}
