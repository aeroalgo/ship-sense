export type Quality =
  | "good"
  | "bad"
  | "uncertain"
  | "stale"
  | "quarantine";

export type AggregateStatus = Quality | "unknown";

export const QUALITIES: readonly Quality[] = [
  "good",
  "bad",
  "uncertain",
  "stale",
  "quarantine",
] as const;
