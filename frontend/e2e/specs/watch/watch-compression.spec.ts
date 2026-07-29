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
    quarantine_tags: ["unknown_native_40099"],
    stale_intervals: [
      { from: "2026-07-26T10:00:00Z", to: "2026-07-26T10:05:00Z" },
    ],
    banner: "Часть периода под сверкой — см. quarantine_tags",
  },
  summary: {
    events_count: 4,
    alarms_count: 3,
    protections_count: 1,
    verdict: "Были тревоги по ГЭУ1; защит 1",
  },
  highlights: [],
  tags_snapshot: [],
};

const watchEvents = {
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
      params: { system: "ГЭУ1" },
      quality: null,
    },
    {
      id: "evt_a2",
      ts: "2026-07-26T09:01:00.000Z",
      event_name: "alarm.HH",
      severity: "alarm",
      source: "aps",
      asset_id: "propulsion.geu.engine_1",
      params: { system: "ГЭУ1" },
      quality: null,
    },
    {
      id: "evt_a3",
      ts: "2026-07-26T09:02:00.000Z",
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

test.describe("watch screen s13", () => {
  test("verdict, protections never collapse, debounce, print DQ", async ({
    page,
  }) => {
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

    const qs = new URLSearchParams({
      from: "2026-07-26T08:00:00.000Z",
      to: "2026-07-26T16:00:00.000Z",
    });
    await page.goto(`/watch?${qs.toString()}`);

    await expect(page.getByTestId("watch-page")).toHaveAttribute(
      "data-state",
      "ready",
    );
    await expect(page.getByTestId("watch-verdict")).not.toBeEmpty();

    const protections = page.getByTestId("watch-section-protections");
    await expect(protections.getByText("Защиты / шатдауны")).toBeVisible();
    await expect(protections.getByRole("button")).toHaveCount(0);
    await expect(protections.getByText(/overspeed trip/i)).toBeVisible();

    const debounce = page.getByTestId("debounce-group-row");
    await expect(debounce).toHaveAttribute("data-collapsed", "true");
    await expect(debounce).toContainText("дребезг");

    await page.getByRole("button", { name: "Печать" }).click();
    const printRoot = page.getByTestId("watch-print-root");
    await expect(printRoot.getByTestId("watch-data-quality")).toBeVisible();
    await expect(printRoot.getByText("unknown_native_40099")).toBeVisible();
  });
});
