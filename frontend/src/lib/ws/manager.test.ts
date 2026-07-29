import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import {
  TagBudgetError,
  WS_MAX_TAGS,
  WsManager,
  getWsManager,
  resetWsManagerForTests,
  type WebSocketLike,
} from "./manager";

class MockWebSocket implements WebSocketLike {
  static instances: MockWebSocket[] = [];
  static autoOpen = true;

  readonly url: string;
  readyState = 0;
  onopen: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  sent: string[] = [];

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    if (MockWebSocket.autoOpen) {
      queueMicrotask(() => this.simulateOpen());
    }
  }

  send(data: string): void {
    this.sent.push(data);
  }

  close(code = 1000, reason = ""): void {
    this.readyState = 3;
    this.onclose?.(
      new CloseEvent("close", { code, reason, wasClean: code === 1000 }),
    );
  }

  simulateOpen(): void {
    this.readyState = 1;
    this.onopen?.(new Event("open"));
  }

  simulateMessage(payload: unknown): void {
    this.onmessage?.(
      new MessageEvent("message", { data: JSON.stringify(payload) }),
    );
  }

  simulateServerClose(code = 1006, reason = "abnormal"): void {
    this.readyState = 3;
    this.onclose?.(
      new CloseEvent("close", { code, reason, wasClean: false }),
    );
  }
}

function lastSent(): Record<string, unknown> {
  const ws = MockWebSocket.instances.at(-1);
  expect(ws).toBeDefined();
  const raw = ws!.sent.at(-1);
  expect(raw).toBeDefined();
  return JSON.parse(raw!) as Record<string, unknown>;
}

function allSent(): Record<string, unknown>[] {
  const ws = MockWebSocket.instances.at(-1);
  expect(ws).toBeDefined();
  return ws!.sent.map((raw) => JSON.parse(raw) as Record<string, unknown>);
}

async function flush(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}

describe("WsManager subscribe payload", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    MockWebSocket.autoOpen = true;
    process.env.NEXT_PUBLIC_WS_URL = "ws://localhost:8000/api/stream";
    vi.useRealTimers();
  });

  afterEach(() => {
    resetWsManagerForTests();
    delete process.env.NEXT_PUBLIC_WS_URL;
  });

  it("sends subscribe with channels, tags, snapshot shape", async () => {
    const manager = new WsManager({
      WebSocketImpl: MockWebSocket as unknown as new (url: string) => WebSocketLike,
    });
    manager.connect();
    await flush();

    manager.subscribeValues(["tag-a", "tag-b"], { snapshot: true });

    const payload = lastSent();
    expect(payload.action).toBe("subscribe");
    expect(payload.channels).toEqual(["values"]);
    expect(payload.tags).toEqual(["tag-a", "tag-b"]);
    expect(payload.snapshot).toBe(true);
    expect(typeof payload.subscription_id).toBe("string");
  });

  it("subscribeEvents omits tags and uses events channel", async () => {
    const manager = new WsManager({
      WebSocketImpl: MockWebSocket as unknown as new (url: string) => WebSocketLike,
    });
    manager.connect();
    await flush();

    manager.subscribeEvents();
    const payload = lastSent();
    expect(payload.action).toBe("subscribe");
    expect(payload.channels).toEqual(["events"]);
    expect(payload.tags).toBeUndefined();
  });
});

describe("WsManager tag budget", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    MockWebSocket.autoOpen = true;
    process.env.NEXT_PUBLIC_WS_URL = "ws://localhost:8000/api/stream";
  });

  afterEach(() => {
    resetWsManagerForTests();
    delete process.env.NEXT_PUBLIC_WS_URL;
  });

  it("throws TagBudgetError in strict mode when tags > 100", async () => {
    const manager = new WsManager({
      WebSocketImpl: MockWebSocket as unknown as new (url: string) => WebSocketLike,
    });
    manager.connect();
    await flush();

    const tags = Array.from({ length: WS_MAX_TAGS + 1 }, (_, i) => `t${i}`);
    expect(() => manager.subscribeValues(tags, { strict: true })).toThrow(
      TagBudgetError,
    );
  });

  it("splits subscribe into chunks of max 100 tags", async () => {
    const manager = new WsManager({
      WebSocketImpl: MockWebSocket as unknown as new (url: string) => WebSocketLike,
    });
    manager.connect();
    await flush();

    const tags = Array.from({ length: 150 }, (_, i) => `t${i}`);
    const ids = manager.subscribeValues(tags);
    expect(ids).toHaveLength(2);

    const payloads = allSent().filter((p) => p.action === "subscribe");
    expect(payloads).toHaveLength(2);
    expect((payloads[0]!.tags as string[]).length).toBe(100);
    expect((payloads[1]!.tags as string[]).length).toBe(50);
  });
});

describe("WsManager reconnect + resume", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    MockWebSocket.autoOpen = true;
    process.env.NEXT_PUBLIC_WS_URL = "ws://localhost:8000/api/stream";
    vi.useFakeTimers();
  });

  afterEach(() => {
    resetWsManagerForTests();
    delete process.env.NEXT_PUBLIC_WS_URL;
    vi.useRealTimers();
  });

  it("resubscribes last set with resume_cursor after reconnect", async () => {
    const manager = new WsManager({
      WebSocketImpl: MockWebSocket as unknown as new (url: string) => WebSocketLike,
      initialBackoffMs: 100,
      maxBackoffMs: 5000,
    });
    const events: string[] = [];
    manager.on((e) => events.push(e.type));

    manager.connect();
    await flush();
    manager.subscribeValues(["tag-a"]);
    await flush();

    const first = MockWebSocket.instances[0]!;
    first.simulateMessage({
      type: "value",
      cursor: 42,
      channel: "values",
      tag_id: "tag-a",
      value: 1,
      quality: "good",
      source_ts: "2026-07-26T16:00:00Z",
      edge_ts: "2026-07-26T16:00:00Z",
    });

    first.simulateServerClose();
    expect(events).toContain("disconnect");
    expect(manager.getStatus()).toBe("reconnecting");

    await vi.advanceTimersByTimeAsync(100);
    await flush();

    expect(MockWebSocket.instances.length).toBe(2);
    const second = MockWebSocket.instances[1]!;
    expect(second.sent.length).toBeGreaterThan(0);

    const resub = second.sent
      .map((raw) => JSON.parse(raw) as Record<string, unknown>)
      .find((p) => p.action === "subscribe");
    expect(resub).toBeDefined();
    expect(resub!.tags).toEqual(["tag-a"]);
    expect(resub!.resume_cursor).toEqual({ values: 42 });
    expect(events).toContain("connected");
  });

  it("emits cursor_expired on CURSOR_EXPIRED error", async () => {
    const manager = new WsManager({
      WebSocketImpl: MockWebSocket as unknown as new (url: string) => WebSocketLike,
    });
    const expired: unknown[] = [];
    manager.on((e) => {
      if (e.type === "cursor_expired") expired.push(e);
    });

    manager.connect();
    await flush();
    manager.subscribeEvents();

    MockWebSocket.instances[0]!.simulateMessage({
      type: "error",
      code: "CURSOR_EXPIRED",
      message: "Resume cursor older than ring buffer",
      channel: "events",
      oldest_available: 800,
      hint: "Refetch GET /api/events?from=...",
    });

    expect(expired).toHaveLength(1);
    expect(expired[0]).toMatchObject({
      type: "cursor_expired",
      channel: "events",
      oldest_available: 800,
    });
  });

  it("emits stale when value quality is stale", async () => {
    const manager = new WsManager({
      WebSocketImpl: MockWebSocket as unknown as new (url: string) => WebSocketLike,
    });
    const staleEvents: unknown[] = [];
    manager.on((e) => {
      if (e.type === "stale") staleEvents.push(e);
    });

    manager.connect();
    await flush();
    MockWebSocket.instances[0]!.simulateMessage({
      type: "value",
      cursor: 1,
      channel: "values",
      tag_id: "tag-a",
      value: 0,
      quality: "stale",
      source_ts: "2026-07-26T16:00:00Z",
      edge_ts: "2026-07-26T16:00:00Z",
    });

    expect(staleEvents).toHaveLength(1);
  });
});

describe("getWsManager singleton", () => {
  afterEach(() => {
    resetWsManagerForTests();
    delete process.env.NEXT_PUBLIC_WS_URL;
  });

  it("returns shared instance", () => {
    process.env.NEXT_PUBLIC_WS_URL = "ws://localhost:8000/api/stream";
    const a = getWsManager({
      WebSocketImpl: MockWebSocket as unknown as new (url: string) => WebSocketLike,
    });
    const b = getWsManager();
    expect(a).toBe(b);
  });
});

describe("useWsChannel cleanup", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    MockWebSocket.autoOpen = true;
    process.env.NEXT_PUBLIC_WS_URL = "ws://localhost:8000/api/stream";
    resetWsManagerForTests();
  });

  afterEach(() => {
    resetWsManagerForTests();
    delete process.env.NEXT_PUBLIC_WS_URL;
  });

  it("unsubscribes on unmount", async () => {
    const { renderHook } = await import("@testing-library/react");
    const { useWsChannel } = await import("@/hooks/useWsChannel");

    getWsManager({
      WebSocketImpl: MockWebSocket as unknown as new (url: string) => WebSocketLike,
    });

    const hook = renderHook(() =>
      useWsChannel({ channels: ["values"], tags: ["tag-a"] }),
    );
    await flush();

    const beforeUnsub = allSent().filter((p) => p.action === "subscribe");
    expect(beforeUnsub.length).toBeGreaterThanOrEqual(1);
    const subId = beforeUnsub[0]!.subscription_id as string;

    hook.unmount();
    await flush();

    const unsub = allSent().find(
      (p) => p.action === "unsubscribe" && p.subscription_id === subId,
    );
    expect(unsub).toBeDefined();
  });
});
