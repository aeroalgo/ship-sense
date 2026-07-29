import { expect, test } from "@playwright/test";

import {
  eventsFixture,
  installTheme,
  mockCommonApis,
  seriesFixture,
  setpointsFixture,
} from "../fixtures/api";

test.describe("PW-04 Trends deep-link from event", () => {
  test("journal event opens trends with chart, setpoint, marker", async ({
    page,
  }) => {
    await installTheme(page);
    await mockCommonApis(page, {
      events: eventsFixture,
      series: seriesFixture,
      setpoints: setpointsFixture,
    });

    await page.goto("/journal");
    await expect(page.getByTestId("journal-page")).toBeVisible();

    await page
      .getByTestId("journal-virtual-list")
      .getByRole("button", { name: "Тренд" })
      .first()
      .click();

    await expect(page).toHaveURL(/\/trends\?/);
    await expect(page).toHaveURL(/tag=TAI4101/);
    await expect(page).toHaveURL(/from=/);
    await expect(page).toHaveURL(/to=/);

    await expect(page.getByTestId("trend-chart")).toBeVisible();
    await expect(page.getByTestId("setpoint-line")).toHaveCount(1);
    await expect(page.getByTestId("event-marker").first()).toBeVisible();
    await expect(page.getByTestId("event-marker").first()).toHaveAttribute(
      "data-marker-ts",
      /2026-07-26T07:58/,
    );
  });
});
