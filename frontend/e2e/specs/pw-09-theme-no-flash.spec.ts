import { expect, test } from "@playwright/test";

import { installTheme, mockCommonApis } from "../fixtures/api";

test.describe("PW-09 Theme day/night/dim no flash", () => {
  test("two clicks reach dim without large white flash", async ({ page }) => {
    await installTheme(page);
    await mockCommonApis(page);

    await page.goto("/overview");
    await expect(page.getByTestId("overview-page")).toBeVisible();

    const html = page.locator("html");
    await expect(html).toHaveAttribute("data-theme", "day");

    const switcher = page.getByTestId("theme-switcher");
    await switcher.click();
    await expect(html).toHaveAttribute("data-theme", "night");
    await switcher.click();
    await expect(html).toHaveAttribute("data-theme", "dim");

    const largeWhite = await page.evaluate(() => {
      const threshold = 10 * 10;
      const all = Array.from(document.querySelectorAll("body *"));
      for (const el of all) {
        const style = getComputedStyle(el);
        const bg = style.backgroundColor;
        if (bg !== "rgb(255, 255, 255)" && bg !== "#ffffff") continue;
        const rect = el.getBoundingClientRect();
        if (rect.width * rect.height > threshold) return true;
      }
      const rootBg = getComputedStyle(document.documentElement).backgroundColor;
      return rootBg === "rgb(255, 255, 255)";
    });
    expect(largeWhite).toBe(false);
  });
});
