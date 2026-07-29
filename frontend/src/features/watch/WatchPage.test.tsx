import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
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

import {
  DATA_QUALITY_PANEL_TEST_ID,
  DEBOUNCE_GROUP_TEST_ID,
  SECTION_TITLES,
  WATCH_SECTION_TEST_ID,
  WATCH_VERDICT_TEST_ID,
} from "@/lib/watch/watch-compression-spec";
import { handlers } from "@/test/msw/handlers";
import { watchReportFixture } from "@/test/msw/fixtures";

import {
  WATCH_PAGE_TEST_ID,
  WATCH_PRINT_ROOT_TEST_ID,
  WatchPage,
} from "./WatchPage";

const mockReplace = vi.fn();
const mockPush = vi.fn();
let mockSearch =
  "from=2026-07-26T08:00:00.000Z&to=2026-07-26T16:00:00.000Z";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
    push: mockPush,
  }),
  useSearchParams: () => new URLSearchParams(mockSearch),
  usePathname: () => "/watch",
}));

const API = "http://localhost:8000";
const server = setupServer(...handlers);

const watchEvents = {
  items: [
    {
      id: "evt_trip",
      ts: "2026-07-26T08:10:00Z",
      event_name: "GEU1 overspeed trip",
      severity: "alarm",
      source: "aps",
      asset_id: "propulsion.geu.engine_1",
      params: { kind: "protection", system: "ГЭУ1" },
      quality: null,
    },
    {
      id: "evt_a1",
      ts: "2026-07-26T09:00:00Z",
      event_name: "alarm.HH",
      severity: "alarm",
      source: "aps",
      asset_id: "propulsion.geu.engine_1",
      params: { system: "ГЭУ1", kks: "TAI4101" },
      quality: null,
    },
    {
      id: "evt_a2",
      ts: "2026-07-26T09:01:00Z",
      event_name: "alarm.HH",
      severity: "alarm",
      source: "aps",
      asset_id: "propulsion.geu.engine_1",
      params: { system: "ГЭУ1", kks: "TAI4101" },
      quality: null,
    },
    {
      id: "evt_a3",
      ts: "2026-07-26T09:02:00Z",
      event_name: "alarm.HH",
      severity: "alarm",
      source: "aps",
      asset_id: "propulsion.geu.engine_1",
      params: { system: "ГЭУ1", kks: "TAI4101" },
      quality: null,
    },
  ],
  next_cursor: null,
  has_more: false,
};

function wrap(ui: React.ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{ui}</QueryClientProvider>;
}

beforeAll(() => {
  process.env.NEXT_PUBLIC_API_URL = API;
  server.listen({ onUnhandledRequest: "error" });
});

beforeEach(() => {
  mockSearch =
    "from=2026-07-26T08:00:00.000Z&to=2026-07-26T16:00:00.000Z";
  mockReplace.mockReset();
  mockPush.mockReset();
  server.use(
    http.get("*/api/events", () => HttpResponse.json(watchEvents)),
    http.get("*/api/reports/watch", () =>
      HttpResponse.json(watchReportFixture),
    ),
  );
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => server.close());

describe("WatchPage", () => {
  it("shows verdict when alarms exist; protections first and not collapsible", async () => {
    render(wrap(<WatchPage />));

    await waitFor(() => {
      expect(screen.getByTestId(WATCH_PAGE_TEST_ID)).toHaveAttribute(
        "data-state",
        "ready",
      );
    });

    const verdict = screen.getByTestId(WATCH_VERDICT_TEST_ID);
    expect(verdict.textContent?.trim().length).toBeGreaterThan(0);
    expect(verdict).toHaveAttribute("data-tone");

    const protections = screen.getByTestId(
      `${WATCH_SECTION_TEST_ID}-protections`,
    );
    const alarms = screen.getByTestId(`${WATCH_SECTION_TEST_ID}-alarms`);
    expect(protections.compareDocumentPosition(alarms)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );

    expect(within(protections).getByText(SECTION_TITLES.protections)).toBeInTheDocument();
    expect(within(protections).queryByRole("button")).toBeNull();
    expect(within(protections).getByText(/overspeed trip/i)).toBeInTheDocument();
  });

  it("collapses debounce alarm groups with count", async () => {
    render(wrap(<WatchPage />));

    await waitFor(() => {
      expect(screen.getByTestId(WATCH_PAGE_TEST_ID)).toHaveAttribute(
        "data-state",
        "ready",
      );
    });

    const row = screen.getByTestId(DEBOUNCE_GROUP_TEST_ID);
    expect(row).toHaveAttribute("data-collapsed", "true");
    expect(row).toHaveAttribute("data-count", "3");
    expect(row).toHaveTextContent(/дребезг/);
  });

  it("print includes data_quality panel", async () => {
    render(wrap(<WatchPage />));

    await waitFor(() => {
      expect(screen.getByTestId(WATCH_PAGE_TEST_ID)).toHaveAttribute(
        "data-state",
        "ready",
      );
    });

    fireEvent.click(screen.getByRole("button", { name: "Печать" }));

    const printRoot = screen.getByTestId(WATCH_PRINT_ROOT_TEST_ID);
    expect(
      within(printRoot).getByTestId(DATA_QUALITY_PANEL_TEST_ID),
    ).toBeInTheDocument();
    expect(
      within(printRoot).getByText("unknown_native_40099"),
    ).toBeInTheDocument();
    expect(within(printRoot).getByText(/Иванов И\.И\./)).toBeInTheDocument();
  });
});
