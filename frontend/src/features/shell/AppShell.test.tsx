import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/overview",
}));

vi.mock("./useStatusBarAlarms", () => ({
  useStatusBarAlarms: () => ({
    alarms: [],
    wsStatus: "idle",
  }),
}));

import { DesignProvider } from "@/features/session/DesignProvider";
import { ThemeProvider } from "@/features/session/ThemeProvider";
import { DESIGN_SWITCHER_TEST_ID } from "@/lib/theme/switcher-spec";
import { THEME_SWITCHER_TEST_ID } from "@/lib/theme/switcher-spec";

vi.mock("@/features/session/useSession", () => ({
  useSession: () => ({
    person: {
      person_id: "ivanov",
      name: "Иванов",
      rank: "вахтенный",
      default_screen: 1,
    },
    logout: vi.fn(),
  }),
}));

import { APP_SHELL_TEST_ID, AppShell } from "./AppShell";

describe("AppShell appearance switchers", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_MOCK = "0";
  });

  it("renders theme and design switchers in the status bar", () => {
    render(
      <ThemeProvider>
        <DesignProvider>
          <AppShell>
            <div>content</div>
          </AppShell>
        </DesignProvider>
      </ThemeProvider>,
    );

    expect(screen.getByTestId(APP_SHELL_TEST_ID)).toBeInTheDocument();
    expect(screen.getByTestId(THEME_SWITCHER_TEST_ID)).toBeInTheDocument();
    expect(screen.getByTestId(DESIGN_SWITCHER_TEST_ID)).toBeInTheDocument();
  });
});
