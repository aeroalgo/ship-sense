import type { Page, WebSocketRoute } from "@playwright/test";

export type WsMockHandle = {
  sockets: WebSocketRoute[];
  closeActive: () => void;
  sendValue: (tagId: string, value: number, quality?: string) => void;
};

export async function installWsMock(page: Page): Promise<WsMockHandle> {
  const sockets: WebSocketRoute[] = [];

  await page.routeWebSocket(/\/api\/stream/, (ws) => {
    sockets.push(ws);
    ws.send(
      JSON.stringify({
        type: "hello",
        protocol: 1,
        server_ts: new Date().toISOString(),
        buffers: { events: 0, values: 0 },
      }),
    );

    ws.onMessage((message) => {
      const raw = typeof message === "string" ? message : message.toString();
      let parsed: { action?: string; subscription_id?: string; channels?: string[] };
      try {
        parsed = JSON.parse(raw) as typeof parsed;
      } catch {
        return;
      }
      if (parsed.action === "subscribe" && parsed.subscription_id) {
        ws.send(
          JSON.stringify({
            type: "ack",
            subscription_id: parsed.subscription_id,
            channels: parsed.channels ?? ["events"],
          }),
        );
      }
    });
  });

  return {
    sockets,
    closeActive: () => {
      const active = sockets[sockets.length - 1];
      if (active) active.close();
    },
    sendValue: (tagId: string, value: number, quality = "good") => {
      const active = sockets[sockets.length - 1];
      if (!active) return;
      const ts = new Date().toISOString();
      active.send(
        JSON.stringify({
          type: "value",
          cursor: Date.now(),
          channel: "values",
          tag_id: tagId,
          value,
          quality,
          source_ts: ts,
          edge_ts: ts,
        }),
      );
    },
  };
}
