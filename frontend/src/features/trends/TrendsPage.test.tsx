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

import { SELECTED_TAGS_TEST_ID, TAG_PICKER_TEST_ID } from "@/components/ds/TagPicker";
import { TREND_CHART_TEST_ID } from "@/lib/trends/chart-lib-spec";
import { handlers } from "@/test/msw/handlers";
import { eventsListFixture, seriesFixture } from "@/test/msw/fixtures";

import {
  EMPTY_PERIOD_COPY,
  TRENDS_PAGE_TEST_ID,
  TrendsPage,
} from "./TrendsPage";

const mockReplace = vi.fn();
const mockPush = vi.fn();
let mockSearch = "";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
    push: mockPush,
  }),
  useSearchParams: () => new URLSearchParams(mockSearch),
  usePathname: () => "/trends",
}));

vi.mock("@/hooks/useWsChannel", () => ({
  useWsChannel: () => undefined,
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

describe("TrendsPage", () => {
  it("deep link prefills tag, window and quick mode", async () => {
    mockSearch =
      "tag=TAI4101&from=2026-07-26T07:50:00.000Z&to=2026-07-26T08:10:00.000Z&mode=quick";

    render(wrap(<TrendsPage />));

    await waitFor(() => {
      expect(screen.getByTestId(TRENDS_PAGE_TEST_ID)).toHaveAttribute(
        "data-state",
        "ready",
      );
    });

    expect(screen.getByTestId(TRENDS_PAGE_TEST_ID)).toHaveAttribute(
      "data-mode",
      "quick",
    );
    expect(screen.getByTestId(TRENDS_PAGE_TEST_ID)).toHaveAttribute(
      "data-live",
      "on",
    );

    const picker = screen.getByTestId(TAG_PICKER_TEST_ID);
    expect(within(picker).getByLabelText("Добавить тег")).toBeInTheDocument();
    const selected = screen.getByTestId(SELECTED_TAGS_TEST_ID);
    expect(within(selected).getByText(/TAI4101/)).toBeInTheDocument();
    expect(picker.contains(selected)).toBe(false);

    expect(screen.getByTestId(TREND_CHART_TEST_ID)).toBeInTheDocument();
    expect(screen.getByTestId("trends-range-label")).toHaveTextContent(
      "2026-07-26T07:50:00.000Z",
    );
    expect(screen.getByTestId("trends-range-label")).toHaveTextContent(
      "2026-07-26T08:10:00.000Z",
    );
    expect(screen.getByTestId("trends-mode-quick")).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("chart tag label matches selected TagPicker names, not API series.name", async () => {
    mockSearch =
      "tag=TAI4101&from=2026-07-26T07:50:00.000Z&to=2026-07-26T08:10:00.000Z&mode=quick";

    render(wrap(<TrendsPage />));

    await waitFor(() => {
      expect(screen.getByTestId(TREND_CHART_TEST_ID)).toBeInTheDocument();
    });

    const selected = screen.getByTestId(SELECTED_TAGS_TEST_ID);
    const chipLabel = within(selected).getByRole("button").textContent ?? "";
    expect(chipLabel).toMatch(/TAI4101/);
    expect(chipLabel).not.toBe(seriesFixture.name);

    const chart = screen.getByTestId(TREND_CHART_TEST_ID);
    expect(within(chart).getByText(chipLabel)).toBeInTheDocument();
    expect(chart.getAttribute("aria-label")).toContain(chipLabel);
    expect(within(chart).queryByText(seriesFixture.name)).toBeNull();
  });

  it("marker click navigates journal intent", async () => {
    mockSearch =
      "tag=TAI4101&from=2026-07-26T07:50:00.000Z&to=2026-07-26T08:10:00.000Z&mode=quick";

    server.use(
      http.get(`${API}/api/events`, () =>
        HttpResponse.json({
          items: [eventsListFixture.items[0]],
          next_cursor: null,
          has_more: false,
        }),
      ),
    );

    render(wrap(<TrendsPage />));

    await waitFor(() => {
      expect(screen.getByTestId(TREND_CHART_TEST_ID)).toBeInTheDocument();
    });

    const markerBtn = await within(
      screen.getByTestId("trend-chart-markers"),
    ).findByRole("button", { name: "alarm.HH" });
    fireEvent.click(markerBtn);

    expect(mockPush).toHaveBeenCalledTimes(1);
    const href = mockPush.mock.calls[0][0] as string;
    const url = new URL(href, "http://localhost");
    expect(url.pathname).toBe("/journal");
    expect(url.searchParams.get("event_name")).toBe("alarm.HH");
    expect(url.searchParams.get("highlight")).toBe("evt_00001234");
    expect(url.searchParams.get("from")).toBeTruthy();
    expect(url.searchParams.get("to")).toBeTruthy();
  });

  it("empty period shows operator copy", async () => {
    mockSearch =
      "tag=TAI4101&from=2026-07-26T07:50:00.000Z&to=2026-07-26T08:10:00.000Z&mode=quick";

    server.use(
      http.get(`${API}/api/series`, () =>
        HttpResponse.json({
          ...seriesFixture,
          tag_id: "TAI4101",
          name: "TAI4101",
          points: [],
        }),
      ),
    );

    render(wrap(<TrendsPage />));

    await waitFor(() => {
      expect(screen.getByTestId(TRENDS_PAGE_TEST_ID)).toHaveAttribute(
        "data-state",
        "empty",
      );
    });

    expect(screen.getByText(EMPTY_PERIOD_COPY)).toBeInTheDocument();
    expect(screen.queryByTestId(TREND_CHART_TEST_ID)).toBeNull();
  });
});
