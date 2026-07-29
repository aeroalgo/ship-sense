"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo, useState } from "react";

import { useWsChannel } from "@/hooks/useWsChannel";
import { queryKeys } from "@/lib/api/query-keys";
import type { SeriesResponse } from "@/lib/api/types";
import type { WsManagerEvent } from "@/lib/ws/types";
import { WS_MAX_TAGS } from "@/lib/ws/types";

export type UseTrendRealtimeResult = {
  valuesStale: boolean;
  live: boolean;
  setLive: (live: boolean) => void;
};

export function useTrendRealtime(
  tags: readonly string[],
  from: string | null,
  to: string | null,
  mode: "quick" | "extended",
  liveOverride: boolean | undefined = undefined,
): UseTrendRealtimeResult {
  const queryClient = useQueryClient();
  const [valuesStale, setValuesStale] = useState(false);
  const [liveManual, setLiveManual] = useState(false);

  const live =
    liveOverride !== undefined
      ? liveOverride
      : mode === "quick"
        ? true
        : liveManual;

  const cappedTags = useMemo(
    () => tags.slice(0, WS_MAX_TAGS),
    [tags],
  );

  const onEvent = useCallback(
    (event: WsManagerEvent) => {
      if (event.type === "stale") {
        setValuesStale(true);
        return;
      }

      if (event.type === "connected") {
        setValuesStale(false);
        return;
      }

      if (event.type !== "value") return;

      const msg = event.message;
      if (msg.quality === "stale") {
        setValuesStale(true);
      } else if (msg.quality === "good") {
        setValuesStale(false);
      }

      if (!from || !to || !cappedTags[0]) return;
      if (!cappedTags.includes(msg.tag_id) && msg.tag_id !== cappedTags[0]) {
        const matchesKks = cappedTags.some(
          (t) => msg.tag_id.includes(t) || t.includes(msg.tag_id),
        );
        if (!matchesKks && msg.tag_id !== cappedTags[0]) {
          return;
        }
      }

      const seriesKey = queryKeys.series({
        tag: cappedTags[0],
        from,
        to,
        resolution: "auto",
      });

      queryClient.setQueryData<SeriesResponse>(seriesKey, (prev) => {
        if (!prev) return prev;
        const point = {
          ts: msg.source_ts,
          value: msg.value,
          quality: msg.quality,
        };
        const last = prev.points[prev.points.length - 1];
        if (last && last.ts === point.ts) {
          return {
            ...prev,
            points: [...prev.points.slice(0, -1), point],
          };
        }
        return {
          ...prev,
          points: [...prev.points, point],
        };
      });
    },
    [queryClient, from, to, cappedTags],
  );

  useWsChannel({
    channels: ["values"],
    tags: cappedTags,
    enabled: live && cappedTags.length > 0,
    snapshot: true,
    onEvent,
  });

  return {
    valuesStale,
    live,
    setLive: setLiveManual,
  };
}
