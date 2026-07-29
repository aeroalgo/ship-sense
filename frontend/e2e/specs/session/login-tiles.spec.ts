import { expect, test } from "@playwright/test";

const API = "http://localhost:8000";

const roster = {
  items: [
    {
      person_id: "ivanov",
      name: "Иванов И.И.",
      rank: "вахтенный механик",
      tile_order: 1,
      active: true,
      default_screen: 1,
    },
    {
      person_id: "petrov",
      name: "Петров П.П.",
      rank: "старший механик",
      tile_order: 2,
      active: true,
      default_screen: 6,
    },
    {
      person_id: "sidorov",
      name: "Сидоров С.С.",
      rank: "электромеханик",
      tile_order: 3,
      active: true,
      default_screen: 1,
    },
  ],
};

test.describe("PW-01 login tiles ≤2 taps", () => {
  test("tap tile creates session and shows chip on overview", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.setItem("shipsense-theme", "day");
      localStorage.setItem("shipsense-design", "d01");
      sessionStorage.clear();
    });

    await page.route(`${API}/api/watch/roster`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(roster),
      });
    });

    await page.route(`${API}/api/session`, async (route) => {
      if (route.request().method() === "POST") {
        const body = route.request().postDataJSON() as { person_id?: string };
        const person = roster.items.find((p) => p.person_id === body.person_id);
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          headers: {
            "Set-Cookie":
              "shipsense_session=e2e-session; Path=/; SameSite=Lax",
          },
          body: JSON.stringify({
            session_id: "550e8400-e29b-41d4-a716-446655440000",
            person_id: person?.person_id ?? "ivanov",
            name: person?.name ?? "Иванов И.И.",
            rank: person?.rank ?? "вахтенный механик",
            started_at: "2026-07-26T16:00:00Z",
            expires_at: "2026-07-27T00:00:00Z",
            token: "e2e-token",
            default_screen: person?.default_screen ?? 1,
          }),
        });
        return;
      }
      if (route.request().method() === "DELETE") {
        await route.fulfill({ status: 204 });
        return;
      }
      await route.continue();
    });

    await page.route(`${API}/api/events**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], next_cursor: null, has_more: false }),
      });
    });

    await page.goto("/login");

    const tiles = page.getByTestId("login-tile");
    await expect(tiles).toHaveCount(3);

    await page.locator('[data-testid="login-tile"][data-person-id="ivanov"]').click();

    await expect(page).toHaveURL(/\/overview/);
    await expect(page.getByTestId("session-chip")).toContainText("Иванов");
  });
});
