import { expect, test } from "@playwright/test";

import {
  installTheme,
  mockCommonApis,
  watchEventsFixture,
  watchReportFixture,
} from "../fixtures/api";

test.describe("PW-05 Watch prototype print", () => {
  test("verdict and print sections with data quality", async ({ page }) => {
    await installTheme(page);
    await mockCommonApis(page, {
      events: watchEventsFixture,
      watchReport: watchReportFixture,
    });

    const qs = new URLSearchParams({
      from: "2026-07-26T08:00:00.000Z",
      to: "2026-07-26T16:00:00.000Z",
    });
    await page.goto(`/watch?${qs.toString()}`);

    await expect(page.getByTestId("watch-page")).toHaveAttribute(
      "data-state",
      "ready",
    );
    await expect(page.getByTestId("watch-verdict")).not.toBeEmpty();

    await page.getByRole("button", { name: "Печать" }).click();
    await page.emulateMedia({ media: "print" });

    const printRoot = page.getByTestId("watch-print-root");
    await expect(printRoot).toBeVisible();
    await expect(printRoot).toContainText(/Защит/i);
    await expect(printRoot).toContainText(/тревог|alarm|ГЭУ/i);
    await expect(printRoot.getByTestId("watch-data-quality")).toBeVisible();
    await expect(printRoot.getByTestId("watch-data-quality")).toContainText(
      "unknown_native_40099",
    );
  });
});
