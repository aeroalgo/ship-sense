import {
  TagBudgetError,
  WS_MAX_TAGS,
  type ResumeCursor,
  type WsChannel,
  type WsClientAction,
  type WsConnectionStatus,
  type WsListener,
  type WsManagerEvent,
  type WsServerMessage,
  type WsSubscribeAction,
} from "./types";

export { TagBudgetError, WS_MAX_TAGS } from "./types";

export type WebSocketLike = {
  readonly readyState: number;
  onopen: ((ev: Event) => void) | null;
  onclose: ((ev: CloseEvent) => void) | null;
  onmessage: ((ev: MessageEvent) => void) | null;
  onerror: ((ev: Event) => void) | null;
  send(data: string): void;
  close(code?: number, reason?: string): void;
};

export type WebSocketConstructor = new (url: string) => WebSocketLike;

export type WsManagerOptions = {
  url?: string;
  WebSocketImpl?: WebSocketConstructor;
  maxTags?: number;
  initialBackoffMs?: number;
  maxBackoffMs?: number;
  reconnect?: boolean;
};

type ActiveSubscription = {
  subscriptionId: string;
  channels: WsChannel[];
  tags: string[];
  snapshot: boolean;
};

const OPEN = 1;

function chunkTags(tags: string[], max: number): string[][] {
  if (tags.length === 0) return [[]];
  const chunks: string[][] = [];
  for (let i = 0; i < tags.length; i += max) {
    chunks.push(tags.slice(i, i + max));
  }
  return chunks;
}

export function getWsUrl(): string {
  const url = process.env.NEXT_PUBLIC_WS_URL;
  if (!url) {
    throw new Error("NEXT_PUBLIC_WS_URL is not set");
  }
  return url;
}

let nextSubSeq = 0;

function createSubscriptionId(prefix: string): string {
  nextSubSeq += 1;
  return `${prefix}-${nextSubSeq}`;
}

export class WsManager {
  private readonly url: string;
  private readonly WebSocketImpl: WebSocketConstructor;
  private readonly maxTags: number;
  private readonly initialBackoffMs: number;
  private readonly maxBackoffMs: number;
  private readonly autoReconnect: boolean;

  private socket: WebSocketLike | null = null;
  private status: WsConnectionStatus = "idle";
  private listeners = new Set<WsListener>();
  private subscriptions = new Map<string, ActiveSubscription>();
  private resumeCursor: ResumeCursor = {};
  private intentionalClose = false;
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(options: WsManagerOptions = {}) {
    this.url = options.url ?? "";
    this.WebSocketImpl =
      options.WebSocketImpl ??
      (globalThis.WebSocket as unknown as WebSocketConstructor);
    this.maxTags = options.maxTags ?? WS_MAX_TAGS;
    this.initialBackoffMs = options.initialBackoffMs ?? 250;
    this.maxBackoffMs = options.maxBackoffMs ?? 5000;
    this.autoReconnect = options.reconnect ?? true;
  }

  getStatus(): WsConnectionStatus {
    return this.status;
  }

  getResumeCursor(): ResumeCursor {
    return { ...this.resumeCursor };
  }

  on(listener: WsListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  connect(): void {
    if (
      this.socket &&
      (this.status === "connecting" ||
        this.status === "connected" ||
        this.status === "reconnecting")
    ) {
      return;
    }
    this.intentionalClose = false;
    this.openSocket();
  }

  disconnect(): void {
    this.intentionalClose = true;
    this.clearReconnectTimer();
    this.reconnectAttempt = 0;
    if (this.socket) {
      this.socket.close(1000, "client disconnect");
      this.socket = null;
    }
    this.status = "disconnected";
    this.emit({ type: "disconnect", reason: "client disconnect" });
  }

  subscribeValues(
    tags: string[],
    options: { snapshot?: boolean; strict?: boolean; subscriptionId?: string } = {},
  ): string[] {
    if (options.strict && tags.length > this.maxTags) {
      throw new TagBudgetError(tags.length, this.maxTags);
    }

    const chunks = chunkTags(tags, this.maxTags);
    const ids: string[] = [];

    for (let i = 0; i < chunks.length; i += 1) {
      const chunk = chunks[i]!;
      const subscriptionId =
        options.subscriptionId && chunks.length === 1
          ? options.subscriptionId
          : createSubscriptionId(
              options.subscriptionId ? `${options.subscriptionId}-p${i}` : "values",
            );

      const sub: ActiveSubscription = {
        subscriptionId,
        channels: ["values"],
        tags: chunk,
        snapshot: options.snapshot ?? true,
      };
      this.subscriptions.set(subscriptionId, sub);
      ids.push(subscriptionId);
      this.sendOrQueue(this.buildSubscribe(sub));
    }

    return ids;
  }

  subscribeEvents(
    options: { subscriptionId?: string } = {},
  ): string {
    const subscriptionId =
      options.subscriptionId ?? createSubscriptionId("events");
    const sub: ActiveSubscription = {
      subscriptionId,
      channels: ["events"],
      tags: [],
      snapshot: false,
    };
    this.subscriptions.set(subscriptionId, sub);
    this.sendOrQueue(this.buildSubscribe(sub));
    return subscriptionId;
  }

  unsubscribe(subscriptionId: string): void {
    if (!this.subscriptions.has(subscriptionId)) return;
    this.subscriptions.delete(subscriptionId);
    this.sendOrQueue({
      action: "unsubscribe",
      subscription_id: subscriptionId,
    });
  }

  private buildSubscribe(sub: ActiveSubscription): WsSubscribeAction {
    const action: WsSubscribeAction = {
      action: "subscribe",
      subscription_id: sub.subscriptionId,
      channels: sub.channels,
      snapshot: sub.snapshot,
    };
    if (sub.channels.includes("values")) {
      action.tags = sub.tags;
    }
    const cursor = this.cursorForChannels(sub.channels);
    if (Object.keys(cursor).length > 0) {
      action.resume_cursor = cursor;
    }
    return action;
  }

  private cursorForChannels(channels: WsChannel[]): ResumeCursor {
    const cursor: ResumeCursor = {};
    if (channels.includes("values") && this.resumeCursor.values !== undefined) {
      cursor.values = this.resumeCursor.values;
    }
    if (channels.includes("events") && this.resumeCursor.events !== undefined) {
      cursor.events = this.resumeCursor.events;
    }
    return cursor;
  }

  private openSocket(): void {
    this.clearReconnectTimer();
    const url = this.url || getWsUrl();
    this.status =
      this.reconnectAttempt > 0 ? "reconnecting" : "connecting";
    const ws = new this.WebSocketImpl(url);
    this.socket = ws;

    ws.onopen = () => {
      this.status = "connected";
      this.reconnectAttempt = 0;
      this.emit({ type: "connected" });
      this.resubscribeAll();
    };

    ws.onmessage = (ev) => {
      this.handleMessage(String(ev.data));
    };

    ws.onerror = () => {
      // close handler drives reconnect
    };

    ws.onclose = (ev) => {
      this.socket = null;
      if (this.intentionalClose) {
        this.status = "disconnected";
        return;
      }
      this.status = "disconnected";
      this.emit({
        type: "disconnect",
        reason: ev.reason || `close ${ev.code}`,
      });
      if (this.autoReconnect) {
        this.scheduleReconnect();
      }
    };
  }

  private scheduleReconnect(): void {
    this.clearReconnectTimer();
    this.reconnectAttempt += 1;
    const delay = Math.min(
      this.maxBackoffMs,
      this.initialBackoffMs * 2 ** (this.reconnectAttempt - 1),
    );
    this.status = "reconnecting";
    this.emit({
      type: "reconnecting",
      attempt: this.reconnectAttempt,
      delayMs: delay,
    });
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.openSocket();
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private resubscribeAll(): void {
    for (const sub of this.subscriptions.values()) {
      this.sendOrQueue(this.buildSubscribe(sub));
    }
  }

  private sendOrQueue(action: WsClientAction): void {
    if (!this.socket || this.socket.readyState !== OPEN) {
      return;
    }
    this.socket.send(JSON.stringify(action));
  }

  private handleMessage(raw: string): void {
    let parsed: WsServerMessage;
    try {
      parsed = JSON.parse(raw) as WsServerMessage;
    } catch {
      return;
    }

    switch (parsed.type) {
      case "hello":
        this.emit({ type: "hello", message: parsed });
        break;
      case "ack":
        this.emit({ type: "ack", message: parsed });
        break;
      case "value":
        this.resumeCursor.values = parsed.cursor;
        this.emit({ type: "value", message: parsed });
        if (parsed.quality === "stale") {
          this.emit({ type: "stale", message: parsed });
        }
        break;
      case "event":
        this.resumeCursor.events = parsed.cursor;
        this.emit({ type: "event", message: parsed });
        break;
      case "pong":
        break;
      case "error":
        if (parsed.code === "CURSOR_EXPIRED") {
          const channel = parsed.channel ?? "events";
          if (channel === "values") {
            delete this.resumeCursor.values;
          } else {
            delete this.resumeCursor.events;
          }
          this.emit({
            type: "cursor_expired",
            channel,
            oldest_available: parsed.oldest_available,
            hint: parsed.hint,
            message: parsed.message,
          });
        } else {
          this.emit({
            type: "error",
            code: parsed.code,
            message: parsed.message,
            channel: parsed.channel,
          });
        }
        break;
      default:
        break;
    }
  }

  private emit(event: WsManagerEvent): void {
    for (const listener of this.listeners) {
      listener(event);
    }
  }
}

let sharedManager: WsManager | null = null;

export function getWsManager(options?: WsManagerOptions): WsManager {
  if (!sharedManager) {
    sharedManager = new WsManager(options);
  }
  return sharedManager;
}

export function resetWsManagerForTests(): void {
  if (sharedManager) {
    sharedManager.disconnect();
  }
  sharedManager = null;
  nextSubSeq = 0;
}
