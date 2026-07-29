"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

import type { EventFiltersValue } from "@/components/ds/EventFilters";
import { useWsChannel } from "@/hooks/useWsChannel";
import { queryKeys } from "@/lib/api/query-keys";
import type { EventItem, EventSeverity, EventsQuery } from "@/lib/api/types";
import type { WsManagerEvent } from "@/lib/ws/types";

import {
  eventMatchesFilters,
  filtersToEventsQuery,
  type JournalFiltersValue,
} from "./journalFilters";
import { sortJournalEvents } from "./journalSort";

type EventsPage = {
  items: EventItem[];
  next_cursor: string | null;
  has_more: boolean;
  reconstruction: string | null;
};

type InfiniteData = {
  pages: EventsPage[];
  pageParams: Array<string | undefined>;
};

export function useEventsRealtime(
  filters: EventFiltersValue | JournalFiltersValue,
  enabled = true,
): void {
  const queryClient = useQueryClient();
  const query: EventsQuery = filtersToEventsQuery(filters);

  const onEvent = useCallback(
    (event: WsManagerEvent) => {
      if (event.type !== "event") return;
      const payload = event.message.event;
      if (!eventMatchesFilters(payload, filters)) return;

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

      queryClient.setQueryData<InfiniteData>(
        queryKeys.events(query),
        (prev) => {
          if (!prev || prev.pages.length === 0) {
            return {
              pages: [
                {
                  items: [item],
                  next_cursor: null,
                  has_more: false,
                  reconstruction: null,
                },
              ],
              pageParams: [undefined],
            };
          }

          const [first, ...rest] = prev.pages;
          if (first.items.some((existing) => existing.id === item.id)) {
            return prev;
          }
          if (
            prev.pages.some((page) =>
              page.items.some((existing) => existing.id === item.id),
            )
          ) {
            return prev;
          }

          const merged = sortJournalEvents([item, ...first.items]);
          return {
            ...prev,
            pages: [{ ...first, items: merged }, ...rest],
          };
        },
      );
    },
    [filters, query, queryClient],
  );

  useWsChannel({
    channels: ["events"],
    enabled,
    onEvent,
  });
}
