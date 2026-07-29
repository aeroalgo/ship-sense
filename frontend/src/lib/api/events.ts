import { apiGet, type ApiResult } from "./client";
import {
  EVENTS_RECONSTRUCTION_HEADER,
  type EventsListResponse,
  type EventsQuery,
} from "./types";

export type FetchEventsResult = ApiResult<EventsListResponse> & {
  reconstruction: string | null;
};

export async function fetchEvents(
  query: EventsQuery = {},
  signal?: AbortSignal,
): Promise<FetchEventsResult> {
  const result = await apiGet<EventsListResponse>("/api/events", {
    query,
    signal,
  });
  return {
    ...result,
    reconstruction: result.headers.get(EVENTS_RECONSTRUCTION_HEADER),
  };
}
