"use client";

import { useCallback, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import type { StatusBarAlarm } from "@/components/ds/StatusBar";
import { useWsChannel } from "@/hooks/useWsChannel";
import { fetchEvents } from "@/lib/api/events";
import { queryKeys } from "@/lib/api/query-keys";
import type { EventItem, EventSeverity } from "@/lib/api/types";
import type { LampSeverity } from "@/lib/ds/lamp-grammar-spec";
import type { WsConnectionStatus, WsManagerEvent } from "@/lib/ws/types";

export type StatusBarAlarmItem = StatusBarAlarm & {
  assetId: string | null;
  from: string;
};

const BOOTSTRAP_QUERY = {
  limit: 20,
  severity: "alarm" as const,
};

function mapEventSeverity(severity: EventSeverity | string | null): LampSeverity {
  if (severity === "alarm") return "alarm";
  if (severity === "warning") return "warning-drift";
  if (severity === "info") return "info";
  return "no-data";
}

function eventToAlarm(item: EventItem): StatusBarAlarmItem {
  const kks =
    typeof item.params?.kks === "string" ? item.params.kks : undefined;
  return {
    id: item.id,
    label: kks ? `${kks} ${item.event_name}` : item.event_name,
    severity: mapEventSeverity(item.severity),
    lifecycle: "active",
    quality: item.quality ?? "good",
    assetId: item.asset_id,
    from: item.ts,
  };
}

function isAlarmSeverity(severity: string | null | undefined): boolean {
  return severity === "alarm";
}

export type UseStatusBarAlarmsResult = {
  alarms: StatusBarAlarmItem[];
  wsStatus: WsConnectionStatus;
  stale: boolean;
  lastEventTs: string | null;
};

export function useStatusBarAlarms(): UseStatusBarAlarmsResult {
  const [alarms, setAlarms] = useState<StatusBarAlarmItem[]>([]);
  const [wsStatus, setWsStatus] = useState<WsConnectionStatus>("idle");
  const [stale, setStale] = useState(false);
  const [lastEventTs, setLastEventTs] = useState<string | null>(null);

  const bootstrap = useQuery({
    queryKey: queryKeys.events(BOOTSTRAP_QUERY),
    queryFn: async ({ signal }) => {
      const result = await fetchEvents(BOOTSTRAP_QUERY, signal);
      return result.data;
    },
    retry: false,
  });

  useEffect(() => {
    if (!bootstrap.data) return;
    const next = bootstrap.data.items
      .filter((item) => isAlarmSeverity(item.severity))
      .map(eventToAlarm);
    setAlarms(next);
    if (next[0]) setLastEventTs(next[0].from);
  }, [bootstrap.data]);

  const onEvent = useCallback((event: WsManagerEvent) => {
    if (event.type === "connected") {
      setWsStatus("connected");
      setStale(false);
      return;
    }
    if (event.type === "reconnecting") {
      setWsStatus("reconnecting");
      setStale(true);
      return;
    }
    if (event.type === "disconnect") {
      setWsStatus("disconnected");
      setStale(true);
      return;
    }
    if (event.type === "event") {
      const payload = event.message.event;
      if (!isAlarmSeverity(payload.severity)) return;
      const item: EventItem = {
        id: payload.id,
        ts: payload.ts,
        event_name: payload.event_name,
        severity: (payload.severity as EventSeverity) ?? null,
        source: payload.source,
        asset_id: payload.asset_id ?? null,
        params: payload.params ?? {},
        quality: null,
      };
      const alarm = eventToAlarm(item);
      setLastEventTs(alarm.from);
      setAlarms((prev) => {
        const without = prev.filter((a) => a.id !== alarm.id);
        return [alarm, ...without].slice(0, 20);
      });
    }
  }, []);

  useWsChannel({
    channels: ["events"],
    onEvent,
  });

  return { alarms, wsStatus, stale, lastEventTs };
}
