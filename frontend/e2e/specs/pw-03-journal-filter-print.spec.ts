import { expect, test } from "@playwright/test";

import { installTheme, mockCommonApis } from "../fixtures/api";
import { installWsMock } from "../fixtures/ws-mock";

test.describe("PW-03 Journal filter + print", () => {
  test("severity=alarm filter and print layout provenance", async ({
    page,
  }) => {
    await installTheme(page);
    await installWsMock(page);
    await mockCommonApis(page);

    await page.goto("/journal");
    await expect(page.getByTestId("journal-page")).toHaveAttribute(
      "data-state",
      "ready",
    );

    const severity = page
      .getByTestId("journal-filters")
      .getByRole("combobox", { name: "Severity" });
    await severity.selectOption("alarm");
    await expect(severity).toHaveValue("alarm");
    await expect(page).toHaveURL(/severity=alarm/);

    const rows = page
      .getByTestId("journal-virtual-list")
      .getByTestId("event-row");
    await expect(rows).toHaveCount(1);
    await expect(rows.first().getByTestId("lamp")).toHaveAttribute(
      "data-severity",
      "alarm",
    );

    await page.getByTestId("print-button").click();
    await page.emulateMedia({ media: "print" });

    const printLayout = page.getByTestId("print-layout");
    await expect(printLayout).toBeVisible();
    await expect(printLayout).toContainText(/достоверность/i);
  });
});
