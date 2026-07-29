import { apiDelete, apiGet, apiPost, type ApiResult } from "./client";
import type {
  RosterResponse,
  SessionCreateRequest,
  SessionResponse,
} from "./types";

export function fetchRoster(
  signal?: AbortSignal,
): Promise<ApiResult<RosterResponse>> {
  return apiGet<RosterResponse>("/api/watch/roster", { signal });
}

export function createSession(
  body: SessionCreateRequest,
  signal?: AbortSignal,
): Promise<ApiResult<SessionResponse>> {
  return apiPost<SessionResponse>("/api/session", body, { signal });
}

export function deleteSession(
  signal?: AbortSignal,
): Promise<ApiResult<void>> {
  return apiDelete("/api/session", { signal });
}
