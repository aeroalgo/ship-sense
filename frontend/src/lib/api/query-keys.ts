import type { EventsQuery, SeriesAggregateQuery, SeriesQuery, WatchReportQuery } from "./types";

export const queryKeys = {
  assetsTree: ["assets", "tree"] as const,
  events: (query: EventsQuery = {}) => ["events", query] as const,
  series: (query: SeriesQuery) => ["series", query] as const,
  seriesAggregate: (query: SeriesAggregateQuery) =>
    ["series", "aggregate", query] as const,
  setpoints: ["setpoints"] as const,
  setpointHistory: (tag: string) => ["setpoints", "history", tag] as const,
  reports: ["reports"] as const,
  watchReport: (query: WatchReportQuery) => ["reports", "watch", query] as const,
  roster: ["watch", "roster"] as const,
  sourcesStatus: ["sources", "status"] as const,
} as const;
