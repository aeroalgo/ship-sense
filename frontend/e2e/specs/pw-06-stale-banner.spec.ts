import { expect, test } from "@playwright/test";

import {
  installTheme,
  mockCommonApis,
  staleSourcesFixture,
} from "../fixtures/api";
import { installWsMock } from "../fixtures/ws-mock";

test.describe("PW-06 Stale banner global", () => {
  test("freshness banner and body data-stale persist across routes", async ({
    page,
  }) => {
    await installTheme(page);
    await installWsMock(page);
    await mockCommonApis(page, { sources: staleSourcesFixture });

    await page.goto("/overview");
    await expect(page.getByTestId("overview-page")).toBeVisible();

    const banner = page.getByTestId("freshness-banner");
    await expect(banner).toBeVisible();
    await expect(banner).toContainText(/связь|устарел/i);
    await expect(page.locator("body")).toHaveAttribute("data-stale", "true");

    await page.getByTestId("nav-journal").click();
    await expect(page).toHaveURL(/\/journal/);
    await expect(page.getByTestId("freshness-banner")).toBeVisible();
    await expect(page.locator("body")).toHaveAttribute("data-stale", "true");
  });
});
