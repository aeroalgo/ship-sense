import { expect, test } from "@playwright/test";

import {
  installTheme,
  mockCommonApis,
  mockRosterAndSession,
} from "../fixtures/api";

test.describe("PW-01 login tiles ≤2 taps", () => {
  test("tap tile creates session and shows chip on overview", async ({
    page,
  }) => {
    await installTheme(page);
    await page.addInitScript(() => {
      sessionStorage.clear();
    });
    await mockRosterAndSession(page);
    await mockCommonApis(page);

    await page.goto("/login");

    const tiles = page.getByTestId("login-tile");
    await expect(tiles).toHaveCount(3);

    await page.evaluate(() => {
      (window as unknown as { __pwClicks?: number }).__pwClicks = 0;
      window.addEventListener(
        "click",
        () => {
          const w = window as unknown as { __pwClicks?: number };
          w.__pwClicks = (w.__pwClicks ?? 0) + 1;
        },
        true,
      );
    });

    await page
      .locator('[data-testid="login-tile"][data-person-id="ivanov"]')
      .click();

    await expect(page).toHaveURL(/\/overview/);
    await expect(page.getByTestId("session-chip")).toContainText("Иванов");
    const clicks = await page.evaluate(
      () => (window as unknown as { __pwClicks?: number }).__pwClicks ?? 0,
    );
    expect(clicks).toBeGreaterThanOrEqual(1);
    expect(clicks).toBeLessThanOrEqual(2);
  });
});
