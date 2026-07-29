import { expect, test } from "@playwright/test";

const API = "http://localhost:8000";

const seriesPayload = {
  tag_id: "TAI4101",
  name: "Температура выхода ГЭУ1",
  unit: "°C",
  from: "2026-07-26T07:50:00.000Z",
  to: "2026-07-26T08:10:00.000Z",
  resolution: "1m",
  points: [
    {
      ts: "2026-07-26T07:55:00.000Z",
      value: 76.2,
      quality: "good",
      min: 75.8,
      max: 76.5,
      samples: 60,
    },
    {
      ts: "2026-07-26T08:00:00.000Z",
      value: null,
      quality: "bad",
      min: null,
      max: null,
      samples: 0,
    },
    {
      ts: "2026-07-26T08:05:00.000Z",
      value: 78.1,
      quality: "good",
      min: 77.9,
      max: 78.4,
      samples: 60,
    },
  ],
};

const setpointsPayload = {
  items: [
    {
      tag_id: "sp_TAI4101_HH",
      value: 80.0,
      unit: "°C",
      label: "HH TAI4101",
      effective_from: "2026-01-15T00:00:00Z",
    },
  ],
};

const eventsPayload = {
  items: [
    {
      id: "evt_alarm",
      ts: "2026-07-26T07:58:12.000Z",
      event_name: "alarm.HH",
      severity: "alarm",
      source: "aps",
      asset_id: "propulsion.geu.engine_1",
      params: { kks: "TAI4101", threshold: 80, value: 82.1 },
      quality: null,
    },
  ],
  next_cursor: null,
  has_more: false,
};

test.describe("trends screen s12", () => {
  test("deep link shows chart; marker opens journal intent", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.setItem("shipsense-theme", "day");
      localStorage.setItem("shipsense-design", "d01");
    });

    await page.route(`${API}/api/series**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(seriesPayload),
      });
    });

    await page.route(`${API}/api/setpoints**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(setpointsPayload),
      });
    });

    await page.route(`${API}/api/events**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(eventsPayload),
      });
    });

    await page.route(`${API}/api/assets/tree`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          root: {
            id: "ship",
            kind: "plant",
            name: "Ship",
            status: "good",
            worst_tag_id: null,
            children: [],
          },
          generated_at: "2026-07-26T08:00:00Z",
        }),
      });
    });

    const qs = new URLSearchParams({
      tag: "TAI4101",
      from: "2026-07-26T07:50:00.000Z",
      to: "2026-07-26T08:10:00.000Z",
      mode: "quick",
    });
    await page.goto(`/trends?${qs.toString()}`);

    await expect(page.getByTestId("trends-page")).toBeVisible();
    await expect(page.getByTestId("trends-page")).toHaveAttribute(
      "data-mode",
      "quick",
    );
    await expect(page.getByTestId("tag-picker")).toBeVisible();
    await expect(page.getByTestId("selected-tags")).toContainText("TAI4101");
    await expect(page.getByTestId("trend-chart")).toBeVisible();
    await expect(page.getByTestId("trend-chart-setpoints")).toContainText(
      "HH TAI4101",
    );

    await page
      .getByTestId("trend-chart-markers")
      .getByRole("button", { name: "alarm.HH" })
      .first()
      .click();
    await expect(page).toHaveURL(/\/journal\?/);
    await expect(page).toHaveURL(/event_name=alarm\.HH/);
    await expect(page).toHaveURL(/highlight=evt_alarm/);
  });
});
