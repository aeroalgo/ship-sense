import { expect, test } from "@playwright/test";

test.describe("theme switcher scenario", () => {
  test("click theme-switcher twice reaches dim without white flash", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.setItem("shipsense-theme", "day");
      localStorage.setItem("shipsense-design", "d01");
    });

    await page.goto("/dev/appearance");

    const html = page.locator("html");
    await expect(html).toHaveAttribute("data-theme", "day");

    const bg = await page.evaluate(() => {
      return getComputedStyle(document.documentElement).backgroundColor;
    });
    expect(bg).not.toBe("rgb(255, 255, 255)");

    const switcher = page.getByTestId("theme-switcher");
    await switcher.click();
    await expect(html).toHaveAttribute("data-theme", "night");
    await switcher.click();
    await expect(html).toHaveAttribute("data-theme", "dim");

    const alarmBefore = await page
      .getByTestId("alarm-critical-sample")
      .evaluate((el) => getComputedStyle(el).color);

    const design = page.getByTestId("design-switcher");
    await expect(design).toBeVisible();
    await design.click();
    await expect(html).toHaveAttribute("data-design", "d02");

    const alarmAfter = await page
      .getByTestId("alarm-critical-sample")
      .evaluate((el) => getComputedStyle(el).color);

    expect(alarmAfter).toBe(alarmBefore);
  });
});
