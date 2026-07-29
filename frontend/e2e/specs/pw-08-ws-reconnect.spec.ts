import { expect, test } from "@playwright/test";

import { installTheme, mockCommonApis } from "../fixtures/api";
import { installWsMock } from "../fixtures/ws-mock";

test.describe("PW-08 WS reconnect", () => {
  test("ws-status reconnecting then connected after close", async ({
    page,
  }) => {
    await installTheme(page);
    const ws = await installWsMock(page);
    await mockCommonApis(page);

    await page.goto("/overview");
    await expect(page.getByTestId("overview-page")).toBeVisible();

    await expect(page.getByTestId("ws-status")).toHaveAttribute(
      "data-status",
      "connected",
      { timeout: 15_000 },
    );

    ws.closeActive();

    await expect(page.getByTestId("ws-status")).toHaveAttribute(
      "data-status",
      "reconnecting",
      { timeout: 10_000 },
    );

    await expect(page.getByTestId("ws-status")).toHaveAttribute(
      "data-status",
      "connected",
      { timeout: 15_000 },
    );

    ws.sendValue("TAI4101", 81.5, "good");
    await expect(page.getByTestId("ws-status")).toHaveAttribute(
      "data-status",
      "connected",
    );
  });
});
