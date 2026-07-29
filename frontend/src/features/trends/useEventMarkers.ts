"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import { fetchEvents } from "@/lib/api/events";
import { queryKeys } from "@/lib/api/query-keys";
import type { EventSeverity } from "@/lib/api/types";
import type { EventMarker } from "@/lib/trends/chart-lib-spec";

function mapSeverity(
  severity: EventSeverity | null,
): EventMarker["severity"] {
  if (severity === "alarm") return "alarm";
  if (severity === "warning") return "warning";
  return "info";
}

export type UseEventMarkersResult = {
  markers: EventMarker[];
  isLoading: boolean;
  isError: boolean;
};

export function useEventMarkers(
  from: string | null,
  to: string | null,
  assetId: string | undefined,
  enabled: boolean,
): UseEventMarkersResult {
  const query = useQuery({
    queryKey: queryKeys.events({
      from: from ?? undefined,
      to: to ?? undefined,
      asset_id: assetId,
      limit: 200,
    }),
    queryFn: async ({ signal }) => {
      const result = await fetchEvents(
        {
          from: from ?? undefined,
          to: to ?? undefined,
          asset_id: assetId,
          limit: 200,
        },
        signal,
      );
      return result.data;
    },
    enabled: enabled && Boolean(from && to),
    retry: false,
  });

  const markers = useMemo(() => {
    return (query.data?.items ?? []).map((item) => ({
      id: item.id,
      ts: item.ts,
      event_name: item.event_name,
      severity: mapSeverity(item.severity),
    }));
  }, [query.data]);

  return {
    markers,
    isLoading: query.isLoading,
    isError: query.isError,
  };
}
