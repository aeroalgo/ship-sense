import { apiGet, type ApiResult } from "./client";
import type {
  SeriesAggregateQuery,
  SeriesAggregateResponse,
  SeriesQuery,
  SeriesResponse,
} from "./types";

export function fetchSeries(
  query: SeriesQuery,
  signal?: AbortSignal,
): Promise<ApiResult<SeriesResponse>> {
  return apiGet<SeriesResponse>("/api/series", { query, signal });
}

export function fetchSeriesAggregate(
  query: SeriesAggregateQuery,
  signal?: AbortSignal,
): Promise<ApiResult<SeriesAggregateResponse>> {
  return apiGet<SeriesAggregateResponse>("/api/series/aggregate", {
    query: {
      tags: query.tags,
      from: query.from,
      to: query.to,
      resolution: query.resolution,
      fn: query.fn,
    },
    signal,
  });
}
