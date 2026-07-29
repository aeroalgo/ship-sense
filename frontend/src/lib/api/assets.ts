import { apiGet, type ApiResult } from "./client";
import type { AssetsTreeResponse } from "./types";

export function fetchAssetsTree(
  signal?: AbortSignal,
): Promise<ApiResult<AssetsTreeResponse>> {
  return apiGet<AssetsTreeResponse>("/api/assets/tree", { signal });
}
