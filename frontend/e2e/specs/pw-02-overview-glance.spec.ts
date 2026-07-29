import { expect, test } from "@playwright/test";

import { installTheme, mockCommonApis } from "../fixtures/api";

test.describe("PW-02 Overview glance readability", () => {
  test("ship status, ≥4 groups, quarantine lamp", async ({ page }) => {
    await installTheme(page);
    await mockCommonApis(page);

    await page.goto("/overview");

    await expect(page.getByTestId("overview-page")).toHaveAttribute(
      "data-state",
      /ready|partial|stale/,
    );
    await expect(page.getByTestId("ship-status")).toBeVisible();

    const groups = page.getByTestId("overview-group");
    await expect(groups).toHaveCount(4);

    const quarantineGroup = page.locator(
      '[data-testid="overview-group"][data-status="quarantine"]',
    );
    await expect(quarantineGroup).toHaveCount(1);
    await expect(quarantineGroup.getByTestId("lamp")).toHaveAttribute(
      "data-quality",
      "quarantine",
    );
  });
});
