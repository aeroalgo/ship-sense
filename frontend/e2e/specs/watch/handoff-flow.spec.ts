import { expect, test } from "@playwright/test";

const API = "http://localhost:8000";

const watchReport = {
  generated_at: "2026-07-26T16:00:00Z",
  watchkeeper: {
    person_id: "ivanov",
    name: "Иванов И.И.",
    rank: "вахтенный механик",
  },
  period: {
    from: "2026-07-26T08:00:00Z",
    to: "2026-07-26T16:00:00Z",
  },
  data_quality: {
    quarantine_tags: [],
    stale_intervals: [],
    banner: null,
  },
  summary: {
    events_count: 1,
    alarms_count: 1,
    protections_count: 0,
    verdict: "Были тревоги по ГЭУ1; защит: 0",
  },
  highlights: [],
  tags_snapshot: [],
};

const watchEvents = {
  items: [
    {
      id: "evt_a1",
      ts: "2026-07-26T09:00:00.000Z",
      event_name: "alarm.HH",
      severity: "alarm",
      source: "aps",
      asset_id: "propulsion.geu.engine_1",
      params: { system: "ГЭУ1" },
      quality: null,
    },
  ],
  next_cursor: null,
  has_more: false,
};

const overviewTree = {
  root: {
    id: "ship",
    kind: "plant",
    name: "Судно",
    status: "ok",
    children: [],
  },
  generated_at: "2026-07-26T16:00:00Z",
};

test.describe("PW-10 handoff watch → overview", () => {
  test("handoff-active-now navigates to overview", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("shipsense-theme", "day");
      localStorage.setItem("shipsense-design", "d01");
    });

    await page.route(`${API}/api/reports/watch**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(watchReport),
      });
    });

    await page.route(`${API}/api/events**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(watchEvents),
      });
    });

    await page.route(`${API}/api/assets/tree**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(overviewTree),
      });
    });

    await page.route(`${API}/api/sources/status`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [] }),
      });
    });

    const qs = new URLSearchParams({
      from: "2026-07-26T08:00:00.000Z",
      to: "2026-07-26T16:00:00.000Z",
    });
    await page.goto(`/watch?${qs.toString()}`);

    await expect(page.getByTestId("watch-page")).toHaveAttribute(
      "data-state",
      "ready",
    );

    await page.getByTestId("handoff-active-now").click();
    await expect(page).toHaveURL(/\/overview/);
    await expect(page.getByTestId("overview-page")).toBeVisible();
  });

  test("anonymous can still use handoff-active-now", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("shipsense-theme", "day");
      localStorage.setItem("shipsense-design", "d01");
      sessionStorage.clear();
    });

    await page.route(`${API}/api/reports/watch**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...watchReport,
          watchkeeper: {
            person_id: "",
            name: "—",
            rank: "—",
          },
        }),
      });
    });

    await page.route(`${API}/api/events**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(watchEvents),
      });
    });

    await page.route(`${API}/api/assets/tree**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(overviewTree),
      });
    });

    await page.route(`${API}/api/sources/status`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [] }),
      });
    });

    await page.goto("/watch");
    await expect(page.getByTestId("watch-page")).toHaveAttribute(
      "data-state",
      "ready",
    );

    const link = page.getByTestId("handoff-active-now");
    await expect(link).toHaveAttribute("href", "/overview");
    await link.click();
    await expect(page).toHaveURL(/\/overview/);
  });
});
