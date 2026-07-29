"use client";

import { useQuery } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/query-keys";
import { fetchSeries, fetchSeriesAggregate } from "@/lib/api/series";
import type { SeriesPoint, SeriesResponse } from "@/lib/api/types";

export type UseSeriesResult = {
  data: SeriesResponse | null;
  points: SeriesPoint[];
  isLoading: boolean;
  isError: boolean;
  isPeriodTooLong: boolean;
  refetch: () => void;
};

export function useSeries(
  tags: readonly string[],
  from: string | null,
  to: string | null,
  enabled: boolean,
): UseSeriesResult {
  const primary = tags[0] ?? null;
  const multi = tags.length > 1;

  const query = useQuery({
    queryKey: multi
      ? queryKeys.seriesAggregate({
          tags: [...tags],
          from: from ?? "",
          to: to ?? "",
          resolution: "auto",
          fn: "avg",
        })
      : queryKeys.series({
          tag: primary ?? "",
          from: from ?? "",
          to: to ?? "",
          resolution: "auto",
        }),
    queryFn: async ({ signal }) => {
      if (!primary || !from || !to) {
        throw new Error("series query requires tag, from, to");
      }
      if (multi) {
        const result = await fetchSeriesAggregate(
          {
            tags: [...tags],
            from,
            to,
            resolution: "auto",
            fn: "avg",
          },
          signal,
        );
        const first = result.data.series[0];
        if (!first) {
          return {
            tag_id: primary,
            name: primary,
            unit: "",
            from: result.data.from,
            to: result.data.to,
            resolution: result.data.resolution,
            points: [],
          } satisfies SeriesResponse;
        }
        return {
          tag_id: first.tag_id,
          name: first.tag_id,
          unit: first.unit,
          from: result.data.from,
          to: result.data.to,
          resolution: result.data.resolution,
          points: first.points,
        } satisfies SeriesResponse;
      }
      const result = await fetchSeries(
        { tag: primary, from, to, resolution: "auto" },
        signal,
      );
      return result.data;
    },
    enabled: enabled && Boolean(primary && from && to),
    retry: false,
  });

  const isPeriodTooLong =
    query.error instanceof ApiError && query.error.status === 413;

  return {
    data: query.data ?? null,
    points: query.data?.points ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    isPeriodTooLong,
    refetch: () => {
      void query.refetch();
    },
  };
}
