import { apiGet, type ApiResult } from "./client";
import type { SetpointHistoryResponse, SetpointsResponse } from "./types";

export function fetchSetpoints(
  signal?: AbortSignal,
): Promise<ApiResult<SetpointsResponse>> {
  return apiGet<SetpointsResponse>("/api/setpoints", { signal });
}

export function fetchSetpointHistory(
  tag: string,
  signal?: AbortSignal,
): Promise<ApiResult<SetpointHistoryResponse>> {
  return apiGet<SetpointHistoryResponse>("/api/setpoints/history", {
    query: { tag },
    signal,
  });
}
