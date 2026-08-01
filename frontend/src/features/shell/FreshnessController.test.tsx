import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FRESHNESS_BANNER_TEST_ID } from "@/components/ds/FreshnessBanner";
import { QUARANTINE_BANNER_TEST_ID } from "@/components/ds/QuarantineBanner";

import {
  APP_ROOT_ID,
  FRESHNESS_CHROME_TEST_ID,
  FreshnessController,
} from "./FreshnessController";

const useStaleGateMock = vi.fn();
const sourcesQueryMock = vi.fn();

vi.mock("@/hooks/useStaleGate", () => ({
  useStaleGate: (args: unknown) => useStaleGateMock(args),
}));

vi.mock("@/hooks/useWsChannel", () => ({
  useWsChannel: () => undefined,
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: () => sourcesQueryMock(),
}));

function queryResult(data: unknown = undefined) {
  return { data, isLoading: false, isError: false };
}

describe("FreshnessController", () => {
  afterEach(() => {
    cleanup();
    document.body.removeAttribute("data-stale");
  });

  beforeEach(() => {
    useStaleGateMock.mockReset();
    useStaleGateMock.mockReturnValue({
      stale: true,
      lastTs: "2026-07-26T10:00:00Z",
    });
    sourcesQueryMock.mockReset();
    sourcesQueryMock.mockReturnValue(queryResult());
  });

  it("when stale is true, body data-stale is set and freshness banner is visible", () => {
    useStaleGateMock.mockImplementation(
      (args: { lastFreshTs: string | null; forceStale?: boolean }) => {
        document.body.setAttribute("data-stale", "true");
        return { stale: true, lastTs: args.lastFreshTs };
      },
    );

    render(
      <div>
        <FreshnessController
          lastFreshTs="2026-07-26T10:00:00Z"
          forceStale
          quarantineTags={[]}
        />
        <div id={APP_ROOT_ID}>content</div>
      </div>,
    );

    expect(document.body.getAttribute("data-stale")).toBe("true");
    expect(screen.getByTestId(FRESHNESS_BANNER_TEST_ID)).toBeInTheDocument();
    expect(screen.getByTestId(FRESHNESS_BANNER_TEST_ID)).toHaveAttribute(
      "data-stale",
      "true",
    );
  });

  it("renders quarantine banner from live source status", async () => {
    const useQueryMock = vi.fn().mockReturnValue({
      data: {
        items: [
          {
            source_id: "src-a",
            name: "Источник A",
            connected: true,
            last_poll_ts: null,
            error_count_24h: 1,
            quality_summary: "quarantine",
            tags_active: 2,
            tags_quarantine: 1,
            tags_stale: 0,
          },
        ],
      },
      isLoading: false,
      isError: false,
    });
    vi.doMock("@tanstack/react-query", () => ({
      useQuery: () => useQueryMock(),
    }));

    render(<FreshnessController lastFreshTs={null} forceStale />);

    expect(screen.getByTestId(QUARANTINE_BANNER_TEST_ID)).toHaveTextContent(
      "Источник A",
    );
  });

  it("places freshness chrome outside #app-root so desaturate filter cannot affect banner", () => {
    render(
      <div>
        <FreshnessController
          lastFreshTs="2026-07-26T10:00:00Z"
          forceStale
          quarantineTags={["src-a"]}
          quarantineScope="система"
        />
        <div id={APP_ROOT_ID}>
          <span>desaturated content</span>
        </div>
      </div>,
    );

    const chrome = screen.getByTestId(FRESHNESS_CHROME_TEST_ID);
    const appRoot = document.getElementById(APP_ROOT_ID);
    expect(appRoot).toBeTruthy();
    expect(chrome.contains(appRoot)).toBe(false);
    expect(appRoot!.contains(chrome)).toBe(false);
    expect(chrome.querySelector(`[data-testid="${FRESHNESS_BANNER_TEST_ID}"]`)).toBeTruthy();
    expect(
      chrome.querySelector(`[data-testid="${QUARANTINE_BANNER_TEST_ID}"]`),
    ).toBeTruthy();
    expect(chrome.style.zIndex === "" || Number(chrome.style.zIndex) >= 30).toBe(
      true,
    );
  });
});
