"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo, useState } from "react";

import { useWsChannel } from "@/hooks/useWsChannel";
import { queryKeys } from "@/lib/api/query-keys";
import type { AssetsTreeResponse } from "@/lib/api/types";
import type { WsManagerEvent } from "@/lib/ws/types";
import { WS_MAX_TAGS } from "@/lib/ws/types";

import { applyValueToTree } from "./treeUtils";

export type UseOverviewRealtimeResult = {
  valuesStale: boolean;
};

export function useOverviewRealtime(
  tagIds: readonly string[],
  enabled: boolean,
): UseOverviewRealtimeResult {
  const queryClient = useQueryClient();
  const [valuesStale, setValuesStale] = useState(false);

  const cappedTags = useMemo(
    () => tagIds.slice(0, WS_MAX_TAGS),
    [tagIds],
  );

  const onEvent = useCallback(
    (event: WsManagerEvent) => {
      if (event.type === "stale") {
        setValuesStale(true);
        const msg = event.message;
        queryClient.setQueryData<AssetsTreeResponse>(
          queryKeys.assetsTree,
          (prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              root: applyValueToTree(
                prev.root,
                msg.tag_id,
                msg.value,
                msg.quality,
              ),
            };
          },
        );
        return;
      }

      if (event.type === "value") {
        const msg = event.message;
        if (msg.quality === "stale") {
          setValuesStale(true);
        } else if (msg.quality === "good") {
          setValuesStale(false);
        }
        queryClient.setQueryData<AssetsTreeResponse>(
          queryKeys.assetsTree,
          (prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              root: applyValueToTree(
                prev.root,
                msg.tag_id,
                msg.value,
                msg.quality,
              ),
            };
          },
        );
      }

      if (event.type === "connected") {
        setValuesStale(false);
      }
    },
    [queryClient],
  );

  useWsChannel({
    channels: ["values"],
    tags: cappedTags,
    enabled: enabled && cappedTags.length > 0,
    snapshot: true,
    onEvent,
  });

  return { valuesStale };
}
