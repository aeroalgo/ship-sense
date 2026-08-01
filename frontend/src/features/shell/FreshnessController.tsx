"use client";

import { useCallback, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { FreshnessBanner } from "@/components/ds/FreshnessBanner";
import { QuarantineBanner } from "@/components/ds/QuarantineBanner";
import { useWsChannel } from "@/hooks/useWsChannel";
import { useStaleGate } from "@/hooks/useStaleGate";
import { fetchSourcesStatus } from "@/lib/api/sources";
import { queryKeys } from "@/lib/api/query-keys";
import type { WsManagerEvent } from "@/lib/ws/types";

export const FRESHNESS_CHROME_TEST_ID = "freshness-chrome";
export const APP_ROOT_ID = "app-root";

export type FreshnessControllerProps = {
  lastFreshTs?: string | null;
  forceStale?: boolean;
  quarantineTags?: string[];
  quarantineScope?: string;
};

function earliestPollTs(
  items: Array<{ last_poll_ts: string | null }> | undefined,
): string | null {
  if (!items || items.length === 0) return null;
  let earliest: string | null = null;
  for (const item of items) {
    if (item.last_poll_ts && (earliest === null || item.last_poll_ts < earliest)) {
      earliest = item.last_poll_ts;
    }
  }
  return earliest;
}

function quarantineSourceNames(
  items: Array<{ name: string; tags_quarantine: number }> | undefined,
): string[] {
  if (!items) return [];
  const tags: string[] = [];
  for (const item of items) {
    if (item.tags_quarantine > 0) {
      tags.push(item.name);
    }
  }
  return tags;
}

export function FreshnessController({
  lastFreshTs: lastFreshTsProp,
  forceStale: forceStaleProp,
  quarantineTags: quarantineTagsProp,
  quarantineScope = "система",
}: FreshnessControllerProps = {}) {
  const [wsForceStale, setWsForceStale] = useState(false);
  const [wsLastTs, setWsLastTs] = useState<string | null>(null);

  const sources = useQuery({
    queryKey: queryKeys.sourcesStatus,
    queryFn: async ({ signal }) => {
      const result = await fetchSourcesStatus(signal);
      return result.data;
    },
    staleTime: 30_000,
    retry: false,
    enabled: quarantineTagsProp === undefined || lastFreshTsProp === undefined,
  });

  const onEvent = useCallback((event: WsManagerEvent) => {
    if (event.type === "connected") {
      setWsForceStale(false);
      return;
    }
    if (
      event.type === "reconnecting" ||
      event.type === "disconnect" ||
      event.type === "stale"
    ) {
      setWsForceStale(true);
      if (event.type === "stale") {
        setWsLastTs(event.message.source_ts);
      }
      return;
    }
    if (event.type === "value") {
      setWsLastTs(event.message.source_ts);
      if (event.message.quality === "stale") {
        setWsForceStale(true);
      } else if (event.message.quality === "good") {
        setWsForceStale(false);
      }
      return;
    }
    if (event.type === "event") {
      setWsLastTs(event.message.event.ts);
    }
  }, []);

  useWsChannel({
    channels: ["events"],
    onEvent,
    enabled: forceStaleProp === undefined && lastFreshTsProp === undefined,
  });

  const restLastTs = earliestPollTs(sources.data?.items);
  const lastFreshTs =
    lastFreshTsProp !== undefined
      ? lastFreshTsProp
      : wsLastTs ?? restLastTs;
  const forceStale = forceStaleProp ?? wsForceStale;

  const { stale, lastTs } = useStaleGate({ lastFreshTs, forceStale });

  const quarantineTags = useMemo(() => {
    if (quarantineTagsProp !== undefined) return quarantineTagsProp;
    return quarantineSourceNames(sources.data?.items);
  }, [quarantineTagsProp, sources.data?.items]);

  return (
    <div
      data-testid={FRESHNESS_CHROME_TEST_ID}
      id="freshness-chrome"
      style={{
        position: "relative",
        zIndex: 40,
        background: "var(--surface-0)",
      }}
    >
      <FreshnessBanner lastTs={lastTs} stale={stale} />
      <QuarantineBanner tags={quarantineTags} scope={quarantineScope} />
    </div>
  );
}
