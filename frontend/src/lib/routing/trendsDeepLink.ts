import type { EventItem } from "@/lib/api/types";

export const QUICK_WINDOW_MS = 10 * 60 * 1000;

export function tagFromEvent(event: EventItem): string | null {
  const params = event.params ?? {};
  if (typeof params.kks === "string" && params.kks.length > 0) {
    return params.kks;
  }
  if (typeof params.tag === "string" && params.tag.length > 0) {
    return params.tag;
  }
  if (typeof params.tag_id === "string" && params.tag_id.length > 0) {
    return params.tag_id;
  }
  return null;
}

export function trendsDeepLink(event: EventItem): string | null {
  const tag = tagFromEvent(event);
  if (!tag) return null;
  const ts = Date.parse(event.ts);
  if (Number.isNaN(ts)) return null;

  const from = new Date(ts - QUICK_WINDOW_MS).toISOString();
  const to = new Date(ts + QUICK_WINDOW_MS).toISOString();
  const params = new URLSearchParams({
    tag,
    from,
    to,
    mode: "quick",
  });
  return `/trends?${params.toString()}`;
}
