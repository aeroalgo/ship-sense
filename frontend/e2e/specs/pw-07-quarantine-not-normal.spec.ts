import { expect, test } from "@playwright/test";

import { installTheme, mockCommonApis } from "../fixtures/api";

test.describe("PW-07 Quarantine not-as-normal", () => {
  test("quarantine group is not good and lamp quality quarantine", async ({
    page,
  }) => {
    await installTheme(page);
    await mockCommonApis(page);

    await page.goto("/overview");
    await expect(page.getByTestId("overview-page")).toBeVisible();

    const quarantineGroup = page.locator(
      '[data-testid="overview-group"][data-status="quarantine"]',
    );
    await expect(quarantineGroup).toHaveCount(1);
    await expect(quarantineGroup).not.toHaveAttribute("data-status", "good");
    await expect(quarantineGroup.getByTestId("lamp")).toHaveAttribute(
      "data-quality",
      "quarantine",
    );
  });
});
