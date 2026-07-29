import { expect, test } from "@playwright/test";

test.describe("app shell nav scenario", () => {
  test("StatusBar sticky and nav routes to journal with active class", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.setItem("shipsense-theme", "day");
      localStorage.setItem("shipsense-design", "d01");
    });

    await page.goto("/overview");

    const statusBar = page.getByTestId("status-bar");
    await expect(statusBar).toBeVisible();

    const sticky = await statusBar.evaluate((el) => {
      const shell = el.closest("[data-testid='app-shell']");
      const stickyParent = el.parentElement;
      if (!shell || !stickyParent) return null;
      return getComputedStyle(stickyParent).position;
    });
    expect(sticky).toBe("sticky");

    await expect(page.getByTestId("nav-overview")).toHaveAttribute(
      "data-active",
      "true",
    );
    await expect(page.getByTestId("nav-overview")).toHaveClass(
      /app-nav__link--active/,
    );

    await page.getByTestId("nav-journal").click();
    await expect(page).toHaveURL(/\/journal/);
    await expect(page.getByTestId("nav-journal")).toHaveAttribute(
      "data-active",
      "true",
    );
    await expect(page.getByTestId("status-bar")).toBeVisible();
    await expect(page.getByTestId("ws-status")).toBeVisible();
    await expect(page.getByTestId("theme-switcher")).toBeVisible();
  });
});
