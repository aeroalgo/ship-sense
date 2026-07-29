import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  afterAll,
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { SESSION_CHIP_TEST_ID } from "@/components/ds/SessionChip";
import { LOGIN_TILE_TEST_ID } from "@/components/ds/LoginTile";
import { ApiError, notifyUnauthorized } from "@/lib/api/client";
import { handlers } from "@/test/msw/handlers";
import { rosterFixture, sessionFixture } from "@/test/msw/fixtures";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => "/login",
}));

import { LoginPage } from "./LoginPage";
import { DesignProvider } from "./DesignProvider";
import { ThemeProvider } from "./ThemeProvider";
import {
  SESSION_STORAGE_KEY,
  SESSION_TIMEOUT_MESSAGE,
  SessionProvider,
  useSession,
} from "./useSession";

const server = setupServer(...handlers);

function wrap(ui: React.ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <QueryClientProvider client={client}>
      <ThemeProvider>
        <DesignProvider>
          <SessionProvider>{ui}</SessionProvider>
        </DesignProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

function SessionProbe() {
  const { person, logout, toastMessage } = useSession();
  return (
    <div>
      <span data-testid="person-name">{person?.name ?? ""}</span>
      <span data-testid="toast">{toastMessage ?? ""}</span>
      {person ? (
        <button type="button" data-testid="logout-btn" onClick={() => void logout()}>
          logout
        </button>
      ) : null}
    </div>
  );
}

beforeAll(() => {
  process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
  server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
  mockPush.mockReset();
  sessionStorage.clear();
});

afterAll(() => server.close());

beforeEach(() => {
  sessionStorage.clear();
});

describe("session login/logout", () => {
  it("login success redirects to default_screen path", async () => {
    render(wrap(<LoginPage />));

    await waitFor(() => {
      expect(screen.getAllByTestId(LOGIN_TILE_TEST_ID).length).toBeGreaterThan(0);
    });

    const tiles = screen.getAllByTestId(LOGIN_TILE_TEST_ID);
    expect(tiles[0]).toHaveAttribute("data-person-id", "ivanov");

    fireEvent.click(
      document.querySelector(`[data-testid="${LOGIN_TILE_TEST_ID}"][data-person-id="ivanov"]`)!,
    );

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/overview");
    });

    expect(sessionStorage.getItem(SESSION_STORAGE_KEY)).toContain("ivanov");
  });

  it("login as watch mechanic redirects to /watch", async () => {
    render(wrap(<LoginPage />));

    await waitFor(() => {
      expect(screen.getAllByTestId(LOGIN_TILE_TEST_ID).length).toBe(4);
    });

    fireEvent.click(
      document.querySelector(`[data-testid="${LOGIN_TILE_TEST_ID}"][data-person-id="petrov"]`)!,
    );

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/watch");
    });
  });

  it("logout clears session chip person", async () => {
    sessionStorage.setItem(
      SESSION_STORAGE_KEY,
      JSON.stringify({
        person_id: sessionFixture.person_id,
        name: sessionFixture.name,
        rank: sessionFixture.rank,
        default_screen: sessionFixture.default_screen,
      }),
    );

    render(wrap(<SessionProbe />));

    expect(screen.getByTestId("person-name").textContent).toContain("Иванов");

    fireEvent.click(screen.getByTestId("logout-btn"));

    await waitFor(() => {
      expect(screen.getByTestId("person-name").textContent).toBe("");
    });
    expect(sessionStorage.getItem(SESSION_STORAGE_KEY)).toBeNull();
  });

  it("401 clears session and shows timeout toast", async () => {
    sessionStorage.setItem(
      SESSION_STORAGE_KEY,
      JSON.stringify({
        person_id: "ivanov",
        name: "Иванов И.И.",
        rank: "вахтенный механик",
        default_screen: 1,
      }),
    );

    render(wrap(<SessionProbe />));
    expect(screen.getByTestId("person-name").textContent).toContain("Иванов");

    notifyUnauthorized(new ApiError(401, "UNAUTHORIZED", "expired"));

    await waitFor(() => {
      expect(screen.getByTestId("person-name").textContent).toBe("");
      expect(screen.getByTestId("toast").textContent).toBe(SESSION_TIMEOUT_MESSAGE);
    });
    expect(mockPush).toHaveBeenCalledWith("/login");
  });

  it("anonymous mode has no session chip person", () => {
    function ChipProbe() {
      const { person } = useSession();
      return person ? (
        <div data-testid={SESSION_CHIP_TEST_ID}>
          {person.name}
        </div>
      ) : (
        <div data-testid="no-chip" />
      );
    }

    render(wrap(<ChipProbe />));
    expect(screen.getByTestId("no-chip")).toBeInTheDocument();
    expect(screen.queryByTestId(SESSION_CHIP_TEST_ID)).not.toBeInTheDocument();
  });

  it("tiles sorted by tile_order", async () => {
    server.use(
      http.get("http://localhost:8000/api/watch/roster", () =>
        HttpResponse.json({
          items: [
            { ...rosterFixture.items[1], tile_order: 2 },
            { ...rosterFixture.items[0], tile_order: 1 },
          ],
        }),
      ),
    );

    render(wrap(<LoginPage />));

    await waitFor(() => {
      expect(screen.getAllByTestId(LOGIN_TILE_TEST_ID)).toHaveLength(2);
    });

    const tiles = screen.getAllByTestId(LOGIN_TILE_TEST_ID);
    expect(tiles[0]).toHaveAttribute("data-person-id", "ivanov");
    expect(tiles[1]).toHaveAttribute("data-person-id", "petrov");
  });
});
