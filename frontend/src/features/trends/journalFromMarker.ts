import type { EventMarker } from "@/lib/trends/chart-lib-spec";

import { QUICK_WINDOW_MS } from "@/lib/routing/trendsDeepLink";

export function journalDeepLinkFromMarker(marker: EventMarker): string {
  const ts = Date.parse(marker.ts);
  if (Number.isNaN(ts)) {
    throw new Error(`Invalid marker ts: ${marker.ts}`);
  }
  const from = new Date(ts - QUICK_WINDOW_MS).toISOString();
  const to = new Date(ts + QUICK_WINDOW_MS).toISOString();
  const params = new URLSearchParams({
    event_name: marker.event_name,
    from,
    to,
    highlight: marker.id,
  });
  return `/journal?${params.toString()}`;
}
