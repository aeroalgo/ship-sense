import type { Quality } from "@/lib/quality/types";

export const WS_MAX_TAGS = 100;

export const WS_PROTOCOL_VERSION = 1;

export type WsChannel = "values" | "events";

export type ResumeCursor = {
  values?: number;
  events?: number;
};

export type WsHelloMessage = {
  type: "hello";
  protocol: number;
  server_ts: string;
  buffers: { events: number; values: number };
};

export type WsAckMessage = {
  type: "ack";
  subscription_id: string;
  channels: WsChannel[];
  replay?: Partial<Record<WsChannel, number>>;
  oldest_available?: Partial<Record<WsChannel, number>>;
};

export type WsValueMessage = {
  type: "value";
  cursor: number;
  channel: "values";
  tag_id: string;
  value: number | null;
  unit?: string;
  quality: Quality;
  source_ts: string;
  edge_ts: string;
};

export type WsEventPayload = {
  id: string;
  ts: string;
  event_name: string;
  severity: string | null;
  source: string;
  asset_id?: string;
  params?: Record<string, unknown>;
};

export type WsEventMessage = {
  type: "event";
  cursor: number;
  channel: "events";
  event: WsEventPayload;
};

export type WsPongMessage = {
  type: "pong";
  server_ts: string;
};

export type WsErrorMessage = {
  type: "error";
  code: string;
  message: string;
  channel?: WsChannel;
  oldest_available?: number;
  hint?: string;
};

export type WsServerMessage =
  | WsHelloMessage
  | WsAckMessage
  | WsValueMessage
  | WsEventMessage
  | WsPongMessage
  | WsErrorMessage;

export type WsSubscribeAction = {
  action: "subscribe";
  subscription_id: string;
  channels: WsChannel[];
  tags?: string[];
  resume_cursor?: ResumeCursor;
  snapshot?: boolean;
};

export type WsUnsubscribeAction = {
  action: "unsubscribe";
  subscription_id: string;
};

export type WsPingAction = {
  action: "ping";
};

export type WsClientAction =
  | WsSubscribeAction
  | WsUnsubscribeAction
  | WsPingAction;

export type WsManagerEvent =
  | { type: "value"; message: WsValueMessage }
  | { type: "event"; message: WsEventMessage }
  | { type: "stale"; message: WsValueMessage }
  | { type: "disconnect"; reason: string }
  | {
      type: "cursor_expired";
      channel: WsChannel;
      oldest_available?: number;
      hint?: string;
      message: string;
    }
  | { type: "connected" }
  | { type: "reconnecting"; attempt: number; delayMs: number }
  | { type: "hello"; message: WsHelloMessage }
  | { type: "ack"; message: WsAckMessage }
  | { type: "error"; code: string; message: string; channel?: WsChannel };

export type WsListener = (event: WsManagerEvent) => void;

export type WsConnectionStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected";

export class TagBudgetError extends Error {
  readonly count: number;
  readonly max: number;

  constructor(count: number, max: number = WS_MAX_TAGS) {
    super(`WS tag budget exceeded: ${count} > ${max}`);
    this.name = "TagBudgetError";
    this.count = count;
    this.max = max;
  }
}
