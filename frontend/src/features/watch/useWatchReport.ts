"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchEvents } from "@/lib/api/events";
import { queryKeys } from "@/lib/api/query-keys";
import { fetchWatchReport } from "@/lib/api/reports";
import type { EventItem, WatchReportResponse } from "@/lib/api/types";

import {
  collapseDebounceGroups,
  eventsFromHighlights,
  resolveVerdict,
  splitWatchEvents,
  verdictCountConflict,
  type DebounceEventLike,
  type DebounceGroup,
  type VerdictResult,
} from "./debounce";

export type WatchReportView = {
  report: WatchReportResponse;
  protections: DebounceEventLike[];
  alarmGroups: DebounceGroup[];
  memberTimestamps: Record<string, string>;
  systemLabels: string[];
  verdict: VerdictResult;
  verdictConflict: boolean;
  clientVerdictText: string;
};

function toDebounceEvents(items: EventItem[]): DebounceEventLike[] {
  return items.map((item) => ({
    id: item.id,
    ts: item.ts,
    event_name: item.event_name,
    asset_id: item.asset_id,
    severity: item.severity,
    source: item.source,
    params: item.params,
  }));
}

function collectSystemLabels(events: DebounceEventLike[]): string[] {
  const labels = new Set<string>();
  for (const event of events) {
    const system = event.params?.system;
    if (typeof system === "string" && system.trim()) {
      labels.add(system.trim());
      continue;
    }
    const asset = event.asset_id;
    if (asset) {
      const part = asset.split(".").find((p) => /geu|aps|hvac|fuel/i.test(p));
      if (part) {
        labels.add(part.toUpperCase());
      }
    }
  }
  return [...labels];
}

export function buildWatchReportView(
  report: WatchReportResponse,
  events: DebounceEventLike[],
): WatchReportView {
  const { protections, alarms } = splitWatchEvents(events);
  const alarmGroups = collapseDebounceGroups(alarms);
  const memberTimestamps: Record<string, string> = {};
  for (const event of events) {
    memberTimestamps[event.id] = event.ts;
  }
  const systemLabels = collectSystemLabels([...protections, ...alarms]);
  const input = {
    alarms_count: alarms.length,
    protections_count: protections.length,
    system_labels: systemLabels,
    events_count: protections.length + alarms.length,
  };
  const client = resolveVerdict({ serverVerdict: null, input });
  const verdict = resolveVerdict({
    serverVerdict: report.summary.verdict,
    input,
  });
  return {
    report,
    protections,
    alarmGroups,
    memberTimestamps,
    systemLabels,
    verdict,
    verdictConflict: verdictCountConflict(report.summary.verdict, input),
    clientVerdictText: client.text,
  };
}

export function useWatchReport(from: string, to: string) {
  return useQuery({
    queryKey: queryKeys.watchReport({ from, to, format: "json" }),
    queryFn: async ({ signal }): Promise<WatchReportView> => {
      const reportResult = await fetchWatchReport(
        { from, to, format: "json" },
        signal,
      );
      const data = reportResult.data;
      if (typeof data === "string") {
        throw new Error("Ожидался JSON отчёт вахты, получен HTML");
      }

      const fromHighlights = eventsFromHighlights(data.highlights);
      let events: DebounceEventLike[];
      if (fromHighlights) {
        events = fromHighlights;
      } else {
        const eventsResult = await fetchEvents(
          { from, to, limit: 500 },
          signal,
        );
        events = toDebounceEvents(eventsResult.data.items);
      }

      return buildWatchReportView(data, events);
    },
    staleTime: 30_000,
    retry: false,
  });
}
