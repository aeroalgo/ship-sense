"use client";

import { useEffect, useRef } from "react";
import { getWsManager } from "@/lib/ws/manager";
import type { WsChannel, WsListener, WsManagerEvent } from "@/lib/ws/types";

export type UseWsChannelOptions = {
  channels: readonly WsChannel[];
  tags?: readonly string[];
  enabled?: boolean;
  snapshot?: boolean;
  onEvent?: WsListener;
};

export function useWsChannel(options: UseWsChannelOptions): void {
  const { channels, tags = [], enabled = true, snapshot = true, onEvent } =
    options;
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const channelsKey = channels.join(",");
  const tagsKey = tags.join(",");

  useEffect(() => {
    if (!enabled) return;

    const manager = getWsManager();
    manager.connect();

    const subscriptionIds: string[] = [];
    const channelList = channelsKey
      .split(",")
      .filter(Boolean) as WsChannel[];

    if (channelList.includes("values")) {
      const tagList = tagsKey ? tagsKey.split(",") : [];
      subscriptionIds.push(
        ...manager.subscribeValues(tagList, { snapshot }),
      );
    }
    if (channelList.includes("events")) {
      subscriptionIds.push(manager.subscribeEvents());
    }

    const off = manager.on((event: WsManagerEvent) => {
      onEventRef.current?.(event);
    });

    return () => {
      off();
      for (const id of subscriptionIds) {
        manager.unsubscribe(id);
      }
    };
  }, [channelsKey, tagsKey, enabled, snapshot]);
}
