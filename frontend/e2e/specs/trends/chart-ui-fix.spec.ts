import { expect, test } from "@playwright/test";

const API = "http://localhost:8000";

const seriesPayload = {
  tag_id: "TAI4101",
  name: "API-ONLY series name ГД1",
  unit: "°C",
  from: "2026-07-26T07:50:00.000Z",
  to: "2026-07-26T08:10:00.000Z",
  resolution: "1m",
  points: [
    {
      ts: "2026-07-26T07:55:00.000Z",
      value: 76.2,
      quality: "good",
      min: 75.8,
      max: 76.5,
      samples: 60,
    },
    {
      ts: "2026-07-26T08:05:00.000Z",
      value: 78.1,
      quality: "good",
      min: 77.9,
      max: 78.4,
      samples: 60,
    },
  ],
};

const treePayload = {
  root: {
    id: "ship",
    kind: "plant",
    name: "Ship",
    status: "good",
    worst_tag_id: "TAI4101",
    children: [
      {
        id: "tag_TAI4101",
        kind: "tag",
        tag_id: "TAI4101",
        name: "TAI4101 t° смазочного масла",
        unit: "°C",
        status: "good",
        last_value: 61.8,
        quality: "good",
        children: [],
        worst_tag_id: null,
      },
      {
        id: "tag_LA1611",
        kind: "tag",
        tag_id: "LA1611",
        name: "LA1611 низкий уровень",
        unit: "-",
        status: "good",
        last_value: 0,
        quality: "good",
        children: [],
        worst_tag_id: null,
      },
    ],
  },
  generated_at: "2026-07-26T08:00:00Z",
};

test.describe("trends chart UI bugfix", () => {
  test("stroke not black; label matches picker; select stays above chips", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.setItem("shipsense-theme", "day");
      localStorage.setItem("shipsense-design", "d01");
    });

    await page.route(`${API}/api/series**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(seriesPayload),
      });
    });

    await page.route(`${API}/api/setpoints**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [] }),
      });
    });

    await page.route(`${API}/api/events**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], next_cursor: null, has_more: false }),
      });
    });

    await page.route(`${API}/api/assets/tree`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(treePayload),
      });
    });

    const qs = new URLSearchParams({
      tag: "TAI4101",
      from: "2026-07-26T07:50:00.000Z",
      to: "2026-07-26T08:10:00.000Z",
      mode: "quick",
    });
    await page.goto(`/trends?${qs.toString()}`);

    const chart = page.getByTestId("trend-chart");
    await expect(chart).toBeVisible();

    await expect
      .poll(async () => chart.getAttribute("data-series-stroke"))
      .toBeTruthy();
    const stroke = (await chart.getAttribute("data-series-stroke")) ?? "";
    expect(stroke.toLowerCase()).not.toMatch(/^(#000|#000000|black|rgb\(0,\s*0,\s*0\))$/);
    expect(stroke.startsWith("var(")).toBe(false);

    const picker = page.getByTestId("tag-picker");
    const selected = page.getByTestId("selected-tags");
    const chip = selected.getByRole("button").first();
    await expect(chip).toHaveText("TAI4101 t° смазочного масла");
    await expect(chart.getByText("TAI4101 t° смазочного масла")).toBeVisible();
    await expect(chart.getByText("API-ONLY series name ГД1")).toHaveCount(0);

    const pickerHandle = await picker.elementHandle();
    const selectedHandle = await selected.elementHandle();
    expect(pickerHandle && selectedHandle).toBeTruthy();
    const nested = await picker.evaluate(
      (el, other) => el.contains(other as Node),
      selectedHandle,
    );
    expect(nested).toBe(false);

    const select = picker.getByLabel("Добавить тег");
    const selectBox = await select.boundingBox();
    const chipBox = await chip.boundingBox();
    expect(selectBox).toBeTruthy();
    expect(chipBox).toBeTruthy();
    expect(selectBox!.y).toBeLessThan(chipBox!.y);
  });
});
