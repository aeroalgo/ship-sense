"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import type { EventFiltersValue } from "@/components/ds/EventFilters";
import { fetchEvents } from "@/lib/api/events";
import { queryKeys } from "@/lib/api/query-keys";
import type { EventItem } from "@/lib/api/types";

import {
  filtersToEventsQuery,
  type JournalFiltersValue,
} from "./journalFilters";
import { sortJournalEvents } from "./journalSort";

export type UseEventsInfiniteResult = {
  events: EventItem[];
  isLoading: boolean;
  isError: boolean;
  isFetchingNextPage: boolean;
  hasNextPage: boolean;
  fetchNextPage: () => void;
  refetch: () => void;
  reconstruction: string | null;
};

export function useEventsInfinite(
  filters: EventFiltersValue | JournalFiltersValue,
): UseEventsInfiniteResult {
  const query = filtersToEventsQuery(filters);

  const infinite = useInfiniteQuery({
    queryKey: queryKeys.events(query),
    queryFn: async ({ pageParam, signal }) => {
      const result = await fetchEvents(
        {
          ...query,
          cursor: pageParam,
        },
        signal,
      );
      return {
        items: result.data.items,
        next_cursor: result.data.next_cursor,
        has_more: result.data.has_more,
        reconstruction: result.reconstruction,
      };
    },
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) =>
      last.has_more && last.next_cursor ? last.next_cursor : undefined,
    retry: false,
  });

  const events = useMemo(() => {
    const pages = infinite.data?.pages ?? [];
    const flat = pages.flatMap((page) => page.items);
    return sortJournalEvents(flat);
  }, [infinite.data]);

  const reconstruction =
    infinite.data?.pages.find((page) => page.reconstruction)?.reconstruction ??
    null;

  return {
    events,
    isLoading: infinite.isLoading,
    isError: infinite.isError,
    isFetchingNextPage: infinite.isFetchingNextPage,
    hasNextPage: Boolean(infinite.hasNextPage),
    fetchNextPage: () => {
      void infinite.fetchNextPage();
    },
    refetch: () => {
      void infinite.refetch();
    },
    reconstruction,
  };
}
