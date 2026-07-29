"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import { queryKeys } from "@/lib/api/query-keys";
import { fetchSetpoints } from "@/lib/api/setpoints";
import type { SetpointBand } from "@/lib/trends/chart-lib-spec";

function inferKind(label: string): SetpointBand["kind"] {
  const upper = label.toUpperCase();
  if (/\bHH\b/.test(upper) || upper.includes("_HH")) return "HH";
  if (/\bLL\b/.test(upper) || upper.includes("_LL")) return "LL";
  if (/\bH\b/.test(upper) || upper.includes("_H")) return "H";
  if (/\bL\b/.test(upper) || upper.includes("_L")) return "L";
  return "other";
}

function matchesTag(item: { tag_id: string; label: string }, tag: string): boolean {
  return (
    item.tag_id.includes(tag) ||
    item.label.includes(tag) ||
    tag.includes(item.tag_id)
  );
}

export type UseSetpointsResult = {
  bands: SetpointBand[];
  isLoading: boolean;
  isError: boolean;
};

export function useSetpoints(tags: readonly string[]): UseSetpointsResult {
  const query = useQuery({
    queryKey: queryKeys.setpoints,
    queryFn: async ({ signal }) => {
      const result = await fetchSetpoints(signal);
      return result.data;
    },
    staleTime: 60_000,
    retry: false,
    enabled: tags.length > 0,
  });

  const bands = useMemo(() => {
    const items = query.data?.items ?? [];
    if (tags.length === 0) return [];
    return items
      .filter((item) => tags.some((tag) => matchesTag(item, tag)))
      .map((item) => ({
        id: item.tag_id,
        label: item.label,
        value: item.value,
        kind: inferKind(item.label),
        from_ts: item.effective_from,
        to_ts: null,
      }));
  }, [query.data, tags]);

  return {
    bands,
    isLoading: query.isLoading,
    isError: query.isError,
  };
}
