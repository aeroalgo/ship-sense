import { readFileSync } from "node:fs";
import { join } from "node:path";

import type { Page, Route } from "@playwright/test";

export const API = "http://localhost:8000";

function loadJson<T>(name: string): T {
  return JSON.parse(
    readFileSync(join(process.cwd(), "e2e/fixtures", name), "utf8"),
  ) as T;
}

export const rosterFixture = loadJson<{
  items: Array<{
    person_id: string;
    name: string;
    rank: string;
    tile_order: number;
    active: boolean;
    default_screen: number;
  }>;
}>("ship-pack-roster.json");

export const overviewTreeFixture = loadJson<{
  root: unknown;
  generated_at: string;
}>("overview-tree.json");

export const eventsFixture = loadJson<{
  items: Array<Record<string, unknown>>;
  next_cursor: null;
  has_more: boolean;
}>("events.json");

export const seriesFixture = loadJson<Record<string, unknown>>("series.json");

export const setpointsFixture = loadJson<{ items: unknown[] }>("setpoints.json");

export const watchReportFixture = loadJson<Record<string, unknown>>(
  "watch-report.json",
);

export const watchEventsFixture = {
  items: [
    {
      id: "evt_trip",
      ts: "2026-07-26T08:10:00.000Z",
      event_name: "GEU1 overspeed trip",
      severity: "alarm",
      source: "aps",
      asset_id: "propulsion.geu.engine_1",
      params: { kind: "protection", system: "ГЭУ1" },
      quality: null,
    },
    {
      id: "evt_a1",
      ts: "2026-07-26T09:00:00.000Z",
      event_name: "alarm.HH",
      severity: "alarm",
      source: "aps",
      asset_id: "propulsion.geu.engine_1",
      params: { system: "ГЭУ1", kks: "TAI4101" },
      quality: null,
    },
    {
      id: "evt_a2",
      ts: "2026-07-26T09:01:00.000Z",
      event_name: "alarm.HH",
      severity: "alarm",
      source: "aps",
      asset_id: "propulsion.geu.engine_1",
      params: { system: "ГЭУ1", kks: "TAI4101" },
      quality: null,
    },
    {
      id: "evt_a3",
      ts: "2026-07-26T09:02:00.000Z",
      event_name: "alarm.HH",
      severity: "alarm",
      source: "aps",
      asset_id: "propulsion.geu.engine_1",
      params: { system: "ГЭУ1", kks: "TAI4101" },
      quality: null,
    },
  ],
  next_cursor: null,
  has_more: false,
};

export const staleSourcesFixture = {
  items: [
    {
      source_id: "aps",
      name: "АПС",
      connected: false,
      last_poll_ts: "2020-01-01T00:00:00.000Z",
      error_count_24h: 3,
      quality_summary: "stale",
      tags_active: 10,
      tags_quarantine: 0,
      tags_stale: 10,
    },
  ],
};

export const freshSourcesFixture = {
  items: [
    {
      source_id: "aps",
      name: "АПС",
      connected: true,
      last_poll_ts: new Date().toISOString(),
      error_count_24h: 0,
      quality_summary: "good",
      tags_active: 482,
      tags_quarantine: 2,
      tags_stale: 0,
    },
  ],
};

export async function fulfillJson(
  route: Route,
  body: unknown,
  status = 200,
): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

export async function installTheme(page: Page): Promise<void> {
  await page.addInitScript(() => {
    localStorage.setItem("shipsense-theme", "day");
    localStorage.setItem("shipsense-design", "d01");
  });
}

export async function mockCommonApis(
  page: Page,
  options?: {
    tree?: unknown;
    events?: unknown;
    sources?: unknown;
    series?: unknown;
    setpoints?: unknown;
    watchReport?: unknown;
  },
): Promise<void> {
  const tree = options?.tree ?? overviewTreeFixture;
  const events = options?.events ?? eventsFixture;
  const sources = options?.sources ?? freshSourcesFixture;
  const series = options?.series ?? seriesFixture;
  const setpoints = options?.setpoints ?? setpointsFixture;
  const watchReport = options?.watchReport ?? watchReportFixture;

  await page.route(`${API}/api/assets/tree**`, (route) =>
    fulfillJson(route, tree),
  );
  await page.route(`${API}/api/events**`, async (route) => {
    const url = new URL(route.request().url());
    const severity = url.searchParams.get("severity");
    const payload = events as {
      items: Array<{ severity?: string }>;
      next_cursor: null;
      has_more: boolean;
    };
    const items = severity
      ? payload.items.filter((item) => item.severity === severity)
      : payload.items;
    await fulfillJson(route, {
      items,
      next_cursor: null,
      has_more: false,
    });
  });
  await page.route(`${API}/api/sources/status`, (route) =>
    fulfillJson(route, sources),
  );
  await page.route(`${API}/api/series**`, (route) => fulfillJson(route, series));
  await page.route(`${API}/api/setpoints**`, (route) =>
    fulfillJson(route, setpoints),
  );
  await page.route(`${API}/api/reports/watch**`, (route) =>
    fulfillJson(route, watchReport),
  );
}

export async function mockRosterAndSession(page: Page): Promise<void> {
  await page.route(`${API}/api/watch/roster`, (route) =>
    fulfillJson(route, rosterFixture),
  );

  await page.route(`${API}/api/session`, async (route) => {
    if (route.request().method() === "POST") {
      const body = route.request().postDataJSON() as { person_id?: string };
      const person = rosterFixture.items.find(
        (p) => p.person_id === body.person_id,
      );
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        headers: {
          "Set-Cookie": "shipsense_session=e2e-session; Path=/; SameSite=Lax",
        },
        body: JSON.stringify({
          session_id: "550e8400-e29b-41d4-a716-446655440000",
          person_id: person?.person_id ?? "ivanov",
          name: person?.name ?? "Иванов И.И.",
          rank: person?.rank ?? "вахтенный механик",
          started_at: "2026-07-26T16:00:00Z",
          expires_at: "2026-07-27T00:00:00Z",
          token: "e2e-token",
          default_screen: person?.default_screen ?? 1,
        }),
      });
      return;
    }
    if (route.request().method() === "DELETE") {
      await route.fulfill({ status: 204 });
      return;
    }
    await route.continue();
  });
}
