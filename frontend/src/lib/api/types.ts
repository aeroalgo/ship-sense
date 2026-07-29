import type { AggregateStatus, Quality } from "@/lib/quality/types";

export type { AggregateStatus, Quality };

export const EVENTS_RECONSTRUCTION_HEADER = "X-Events-Reconstruction";

export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
};

export type AssetNodeKind = "plant" | "system" | "equipment" | "tag";

export type AssetTreeNode = {
  id: string;
  kind: AssetNodeKind;
  name: string;
  status: AggregateStatus;
  worst_tag_id?: string | null;
  children?: AssetTreeNode[];
  tag_id?: string;
  unit?: string;
  last_value?: number | null;
  last_quality?: Quality;
};

export type AssetsTreeResponse = {
  root: AssetTreeNode;
  generated_at: string;
};

export type SeriesPoint = {
  ts: string;
  value: number | null;
  quality: Quality;
  min?: number | null;
  max?: number | null;
  samples?: number;
};

export type SeriesResponse = {
  tag_id: string;
  name: string;
  unit: string;
  from: string;
  to: string;
  resolution: string;
  points: SeriesPoint[];
};

export type SeriesAggregateItem = {
  tag_id: string;
  unit: string;
  points: SeriesPoint[];
};

export type SeriesAggregateResponse = {
  from: string;
  to: string;
  resolution: string;
  series: SeriesAggregateItem[];
};

export type EventSeverity = "info" | "warning" | "alarm";

export type EventSource = "aps" | "geu" | "edge" | "session";

export type EventItem = {
  id: string;
  ts: string;
  event_name: string;
  severity: EventSeverity | null;
  source: EventSource | string;
  asset_id: string | null;
  params: Record<string, unknown>;
  quality: Quality | null;
};

export type EventsListResponse = {
  items: EventItem[];
  next_cursor: string | null;
  has_more: boolean;
};

export type SetpointItem = {
  tag_id: string;
  value: number;
  unit: string;
  label: string;
  effective_from: string;
};

export type SetpointsResponse = {
  items: SetpointItem[];
};

export type SetpointHistorySegment = {
  from_ts: string;
  to_ts: string | null;
  value: number;
};

export type SetpointHistoryResponse = {
  tag_id: string;
  segments: SetpointHistorySegment[];
};

export type ReportCatalogItem = {
  type: string;
  title: string;
  formats: string[];
  description: string;
};

export type ReportsListResponse = {
  items: ReportCatalogItem[];
};

export type WatchReportResponse = {
  generated_at: string;
  watchkeeper: {
    person_id: string;
    name: string;
    rank: string;
  };
  period: { from: string; to: string };
  data_quality: {
    quarantine_tags: string[];
    stale_intervals: Array<{ from: string; to: string }>;
    banner: string;
  };
  summary: {
    events_count: number;
    alarms_count: number;
    protections_count: number;
    verdict: string;
  };
  highlights: unknown[];
  tags_snapshot: Array<{
    tag_id: string;
    name: string;
    avg: number;
    min: number;
    max: number;
    quality_worst: Quality;
  }>;
};

export type RosterPerson = {
  person_id: string;
  name: string;
  rank: string;
  tile_order: number;
  active: boolean;
  default_screen: number;
};

export type RosterResponse = {
  items: RosterPerson[];
};

export type SessionCreateRequest = {
  person_id: string;
};

export type SessionResponse = {
  session_id: string;
  person_id: string;
  name: string;
  rank: string;
  started_at: string;
  expires_at: string;
  token: string;
  default_screen: number;
};

export type SourceStatusItem = {
  source_id: string;
  name: string;
  connected: boolean;
  last_poll_ts: string;
  error_count_24h: number;
  quality_summary: Quality;
  tags_active: number;
  tags_quarantine: number;
  tags_stale: number;
};

export type SourcesStatusResponse = {
  items: SourceStatusItem[];
};

export type EventsQuery = {
  from?: string;
  to?: string;
  event_name?: string | string[];
  severity?: EventSeverity | EventSeverity[];
  asset_id?: string;
  source?: string;
  ack?: boolean;
  cursor?: string;
  limit?: number;
};

export type SeriesQuery = {
  tag: string;
  from: string;
  to: string;
  resolution?: string;
};

export type SeriesAggregateQuery = {
  tags: string[];
  from: string;
  to: string;
  resolution?: string;
  fn?: "avg" | "min" | "max" | "last";
};

export type WatchReportQuery = {
  from: string;
  to: string;
  format?: "json" | "html";
  session_id?: string;
};
