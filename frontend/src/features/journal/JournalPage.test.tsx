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

import { EVENT_ROW_TEST_ID } from "@/components/ds/EventRow";
import { JOURNAL_FILTERS_TEST_ID } from "@/components/ds/EventFilters";
import { EVENTS_RECONSTRUCTION_HEADER } from "@/lib/api/types";
import { handlers } from "@/test/msw/handlers";
import { eventsListFixture } from "@/test/msw/fixtures";

import {
  APS_ACK_FOOTNOTE,
  JOURNAL_PAGE_TEST_ID,
  JournalPage,
} from "./JournalPage";
import { RECONSTRUCTION_BANNER_TEST_ID } from "./ReconstructionBanner";

const mockReplace = vi.fn();
const mockPush = vi.fn();
let mockSearch = "";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
    push: mockPush,
  }),
  useSearchParams: () => new URLSearchParams(mockSearch),
  usePathname: () => "/journal",
}));

vi.mock("@/hooks/useWsChannel", () => ({
  useWsChannel: () => undefined,
}));

vi.mock("@tanstack/react-virtual", () => ({
  useVirtualizer: ({ count }: { count: number }) => ({
    getVirtualItems: () =>
      Array.from({ length: count }, (_, index) => ({
        index,
        key: index,
        start: index * 56,
        size: 56,
        end: (index + 1) * 56,
      })),
    getTotalSize: () => count * 56,
    measureElement: () => undefined,
  }),
}));

const API = "http://localhost:8000";
const server = setupServer(...handlers);

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
  mockSearch = "";
  mockReplace.mockReset();
  mockPush.mockReset();
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => server.close());

describe("JournalPage", () => {
  it("filter narrows list and syncs URL params", async () => {
    server.use(
      http.get("*/api/events", ({ request }) => {
        const severity = new URL(request.url).searchParams.get("severity");
        const items = severity
          ? eventsListFixture.items.filter((item) => item.severity === severity)
          : eventsListFixture.items;
        return HttpResponse.json({
          items,
          next_cursor: null,
          has_more: false,
        });
      }),
    );

    const { rerender } = render(wrap(<JournalPage />));

    await waitFor(() => {
      expect(screen.getByTestId(JOURNAL_PAGE_TEST_ID)).toHaveAttribute(
        "data-state",
        "ready",
      );
    });

    const list = () => screen.getByTestId("journal-virtual-list");
    expect(within(list()).getAllByTestId(EVENT_ROW_TEST_ID).length).toBe(
      eventsListFixture.items.length,
    );

    const filters = screen.getByTestId(JOURNAL_FILTERS_TEST_ID);
    const severitySelect = within(filters).getByDisplayValue("Все");
    fireEvent.change(severitySelect, { target: { value: "alarm" } });

    expect(mockReplace).toHaveBeenCalledWith("/journal?severity=alarm");

    mockSearch = "severity=alarm";
    rerender(wrap(<JournalPage />));

    await waitFor(() => {
      const rows = within(list()).getAllByTestId(EVENT_ROW_TEST_ID);
      const alarms = eventsListFixture.items.filter(
        (item) => item.severity === "alarm",
      );
      expect(rows.length).toBe(alarms.length);
      expect(rows.some((row) => row.textContent?.includes("alarm.HH"))).toBe(
        true,
      );
      expect(
        rows.some((row) => row.textContent?.includes("protection.trip")),
      ).toBe(true);
    });
  });

  it("has no acknowledge control in DOM", async () => {
    server.use(
      http.get(`${API}/api/events`, () =>
        HttpResponse.json({
          items: eventsListFixture.items,
          next_cursor: null,
          has_more: false,
        }),
      ),
    );

    render(wrap(<JournalPage />));

    await waitFor(() => {
      expect(screen.getByTestId(JOURNAL_PAGE_TEST_ID)).toHaveAttribute(
        "data-state",
        "ready",
      );
    });

    expect(screen.queryByRole("button", { name: /квитир/i })).toBeNull();
    expect(screen.queryByText(/квитировать/i)).toBeNull();
    expect(screen.getByTestId("aps-ack-footnote")).toHaveTextContent(
      APS_ACK_FOOTNOTE,
    );
  });

  it("trend click pushes deep link with correct window", async () => {
    server.use(
      http.get(`${API}/api/events`, () =>
        HttpResponse.json({
          items: [eventsListFixture.items[0]],
          next_cursor: null,
          has_more: false,
        }),
      ),
    );

    render(wrap(<JournalPage />));

    await waitFor(() => {
      expect(
        within(screen.getByTestId("journal-virtual-list")).getByTestId(
          EVENT_ROW_TEST_ID,
        ),
      ).toBeInTheDocument();
    });

    fireEvent.click(
      within(screen.getByTestId("journal-virtual-list")).getByRole("button", {
        name: "Тренд",
      }),
    );

    expect(mockPush).toHaveBeenCalledTimes(1);
    const href = mockPush.mock.calls[0][0] as string;
    const url = new URL(href, "http://localhost");
    expect(url.pathname).toBe("/trends");
    expect(url.searchParams.get("tag")).toBe("TAI4101");
    expect(url.searchParams.get("mode")).toBe("quick");
    const ts = Date.parse(eventsListFixture.items[0].ts);
    expect(Date.parse(url.searchParams.get("from")!)).toBe(ts - 600_000);
    expect(Date.parse(url.searchParams.get("to")!)).toBe(ts + 600_000);
  });

  it("shows reconstruction banner from X-Events-Reconstruction", async () => {
    server.use(
      http.get(`${API}/api/events`, () =>
        HttpResponse.json(
          {
            items: eventsListFixture.items,
            next_cursor: null,
            has_more: false,
          },
          {
            headers: { [EVENTS_RECONSTRUCTION_HEADER]: "edge_only" },
          },
        ),
      ),
    );

    render(wrap(<JournalPage />));

    await waitFor(() => {
      expect(
        screen.getByTestId(RECONSTRUCTION_BANNER_TEST_ID),
      ).toBeInTheDocument();
    });
    expect(screen.getByTestId(RECONSTRUCTION_BANNER_TEST_ID)).toHaveAttribute(
      "data-mode",
      "edge_only",
    );
  });

  it("sorts active-unacked alarm above info", async () => {
    server.use(
      http.get(`${API}/api/events`, () =>
        HttpResponse.json({
          items: [
            eventsListFixture.items[1],
            eventsListFixture.items[0],
          ],
          next_cursor: null,
          has_more: false,
        }),
      ),
    );

    render(wrap(<JournalPage />));

    await waitFor(() => {
      expect(
        within(screen.getByTestId("journal-virtual-list")).getAllByTestId(
          EVENT_ROW_TEST_ID,
        ).length,
      ).toBe(2);
    });

    const rows = within(
      screen.getByTestId("journal-virtual-list"),
    ).getAllByTestId(EVENT_ROW_TEST_ID);
    expect(rows[0]).toHaveAttribute("data-event-id", "evt_00001234");
    expect(rows[1]).toHaveAttribute("data-event-id", "evt_00001235");
  });
});
