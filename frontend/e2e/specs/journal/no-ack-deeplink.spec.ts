import { expect, test } from "@playwright/test";

const API = "http://localhost:8000";

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
    {
      id: "evt_info",
      ts: "2026-07-26T08:00:01.000Z",
      event_name: "session_started",
      severity: "info",
      source: "edge",
      asset_id: null,
      params: { session_id: "sess" },
      quality: null,
    },
  ],
  next_cursor: null,
  has_more: false,
};

test.describe("journal screen s10", () => {
  test("no ack button; filter URL; trend deep link", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("shipsense-theme", "day");
      localStorage.setItem("shipsense-design", "d01");
    });

    await page.route(`${API}/api/events**`, async (route) => {
      const url = new URL(route.request().url());
      const severity = url.searchParams.get("severity");
      const items = severity
        ? eventsPayload.items.filter((item) => item.severity === severity)
        : eventsPayload.items;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        headers: {
          "X-Events-Reconstruction": "edge_only",
          "Access-Control-Expose-Headers": "X-Events-Reconstruction",
        },
        body: JSON.stringify({
          items,
          next_cursor: null,
          has_more: false,
        }),
      });
    });

    await page.route(`${API}/api/sources/status`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [] }),
      });
    });

    await page.goto("/journal");

    await expect(page.getByTestId("journal-page")).toBeVisible();
    await expect(page.getByTestId("reconstruction-banner")).toBeVisible();
    await expect(page.getByTestId("aps-ack-footnote")).toContainText(
      "Квитируется на панели АПС",
    );
    await expect(page.getByRole("button", { name: /квитир/i })).toHaveCount(0);

    await expect(page.getByTestId("journal-virtual-list").getByTestId("event-row")).toHaveCount(2);
    await page.getByTestId("journal-filters").locator("select").selectOption("alarm");
    await expect(page).toHaveURL(/severity=alarm/);

    await expect(page.getByTestId("journal-virtual-list").getByTestId("event-row")).toHaveCount(1);

    await page.getByTestId("journal-virtual-list").getByRole("button", { name: "Тренд" }).click();
    await expect(page).toHaveURL(/\/trends\?/);
    await expect(page).toHaveURL(/tag=TAI4101/);
    await expect(page).toHaveURL(/mode=quick/);
    await expect(page).toHaveURL(/from=/);
    await expect(page).toHaveURL(/to=/);
  });
});
