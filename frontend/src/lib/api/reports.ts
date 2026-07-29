import { apiGet, type ApiResult } from "./client";
import type {
  ReportsListResponse,
  WatchReportQuery,
  WatchReportResponse,
} from "./types";

export function fetchReports(
  signal?: AbortSignal,
): Promise<ApiResult<ReportsListResponse>> {
  return apiGet<ReportsListResponse>("/api/reports", { signal });
}

export function fetchWatchReport(
  query: WatchReportQuery,
  signal?: AbortSignal,
): Promise<ApiResult<WatchReportResponse | string>> {
  return apiGet<WatchReportResponse | string>("/api/reports/watch", {
    query: {
      from: query.from,
      to: query.to,
      format: query.format ?? "json",
      session_id: query.session_id,
    },
    signal,
  });
}
