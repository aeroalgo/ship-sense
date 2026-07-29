import { expect, test } from "@playwright/test";

import {
  installTheme,
  mockCommonApis,
  mockRosterAndSession,
  watchEventsFixture,
  watchReportFixture,
} from "../fixtures/api";

test.describe("PW-10 Handoff watch → overview", () => {
  test("watch mechanic handoff-active-now navigates to overview", async ({
    page,
  }) => {
    await installTheme(page);
    await mockRosterAndSession(page);
    await mockCommonApis(page, {
      events: watchEventsFixture,
      watchReport: watchReportFixture,
    });

    await page.goto("/login");
    await page
      .locator('[data-testid="login-tile"][data-person-id="petrov"]')
      .click();
    await expect(page).toHaveURL(/\/watch/);

    await expect(page.getByTestId("watch-page")).toHaveAttribute(
      "data-state",
      "ready",
    );

    await page.getByTestId("handoff-active-now").click();
    await expect(page).toHaveURL(/\/overview/);
    await expect(page.getByTestId("overview-page")).toBeVisible();
    await expect(page.getByTestId("status-bar")).toBeVisible();
  });
});
