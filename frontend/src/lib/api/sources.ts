import { apiGet, type ApiResult } from "./client";
import type { SourcesStatusResponse } from "./types";

export function fetchSourcesStatus(
  signal?: AbortSignal,
): Promise<ApiResult<SourcesStatusResponse>> {
  return apiGet<SourcesStatusResponse>("/api/sources/status", { signal });
}
