import { expect, test } from "@playwright/test";

const API = "http://localhost:8000";

const overviewTree = {
  root: {
    id: "ship",
    kind: "plant",
    name: "Ледокол",
    status: "uncertain",
    children: [
      {
        id: "aux_bow",
        kind: "system",
        name: "Вспомогательные нос",
        status: "good",
        children: [
          {
            id: "eq1",
            kind: "equipment",
            name: "Насос",
            status: "good",
            children: [
              {
                id: "tag1",
                kind: "tag",
                tag_id: "tag-1",
                name: "P1",
                unit: "bar",
                status: "good",
                last_value: 1,
                last_quality: "good",
              },
            ],
          },
        ],
      },
      {
        id: "propulsion",
        kind: "system",
        name: "Движительная установка",
        status: "uncertain",
        children: [
          {
            id: "geu1",
            kind: "equipment",
            name: "ГЭУ1",
            status: "uncertain",
            children: [
              {
                id: "tag2",
                kind: "tag",
                tag_id: "tag-2",
                name: "T1",
                unit: "°C",
                status: "uncertain",
                last_value: 70,
                last_quality: "uncertain",
              },
            ],
          },
        ],
      },
    ],
  },
  generated_at: "2026-07-26T14:00:00Z",
};

test.describe("overview drill stub T-006", () => {
  test("group click opens stub modal not 404", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("shipsense-theme", "day");
      localStorage.setItem("shipsense-design", "d01");
    });

    await page.route(`${API}/api/assets/tree`, async (route) => {
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

    await page.route(`${API}/api/events**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], next_cursor: null, has_more: false }),
      });
    });

    await page.goto("/overview");

    await expect(page.getByTestId("overview-page")).toBeVisible();
    await expect(page.getByTestId("ship-status")).toBeVisible();
    await expect(page.getByTestId("status-bar")).toBeVisible();

    const groups = page.getByTestId("overview-group");
    await expect(groups.first()).toBeVisible();
    await groups.first().click();

    await expect(page.getByTestId("drill-stub-modal")).toBeVisible();
    await expect(page.getByTestId("drill-stub-modal")).toContainText(
      "Мнемосхема: фаза 2",
    );
    await expect(page).toHaveURL(/\/overview/);
    await expect(page.getByText("404")).toHaveCount(0);
  });
});
