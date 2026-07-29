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
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { LAMP_TEST_ID } from "@/lib/ds/lamp-grammar-spec";
import { OVERVIEW_GROUP_TEST_ID } from "@/components/ds/OverviewGroupCard";
import { SHIP_STATUS_TEST_ID } from "@/components/ds/AggregateShipStatus";
import { STATE_SHELL_TEST_ID } from "@/components/ds/StateShell";
import type { AssetsTreeResponse } from "@/lib/api/types";
import { handlers } from "@/test/msw/handlers";
import { sourcesStatusFixture } from "@/test/msw/fixtures";

import {
  DRILL_STUB_COPY,
  DRILL_STUB_TEST_ID,
} from "./DrillDownStubModal";
import { OverviewPage, OVERVIEW_PAGE_TEST_ID } from "./OverviewPage";
import { rollupTree } from "./treeUtils";

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

const quarantineTree: AssetsTreeResponse = {
  root: {
    id: "ship",
    kind: "plant",
    name: "Ледокол",
    status: "good",
    children: [
      {
        id: "aux_bow",
        kind: "system",
        name: "Вспомогательные нос",
        status: "good",
        children: [
          {
            id: "eq_pump",
            kind: "equipment",
            name: "Насос",
            status: "good",
            children: [
              {
                id: "tag_q",
                kind: "tag",
                tag_id: "tag-quarantine",
                name: "P1",
                unit: "bar",
                status: "quarantine",
                last_value: 1.2,
                last_quality: "quarantine",
              },
              {
                id: "tag_g",
                kind: "tag",
                tag_id: "tag-good",
                name: "P2",
                unit: "bar",
                status: "good",
                last_value: 2.0,
                last_quality: "good",
              },
            ],
          },
        ],
      },
      {
        id: "propulsion",
        kind: "system",
        name: "Движительная установка",
        status: "good",
        children: [
          {
            id: "geu1",
            kind: "equipment",
            name: "ГЭУ1",
            status: "good",
            children: [
              {
                id: "tag_stern",
                kind: "tag",
                tag_id: "tag-stern",
                name: "T1",
                unit: "°C",
                status: "good",
                last_value: 70,
                last_quality: "good",
              },
            ],
          },
        ],
      },
    ],
  },
  generated_at: "2026-07-26T14:00:00Z",
};

beforeAll(() => {
  process.env.NEXT_PUBLIC_API_URL = API;
  server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => server.close());

describe("treeUtils rollup", () => {
  it("client rollup makes quarantine child force group not good", () => {
    const rolled = rollupTree(quarantineTree.root);
    const aux = rolled.children?.find((c) => c.id === "aux_bow");
    expect(aux?.status).toBe("quarantine");
    expect(aux?.status).not.toBe("good");
    expect(rolled.status).toBe("quarantine");
  });
});

describe("OverviewPage", () => {
  it("quarantine child → group Lamp not good", async () => {
    server.use(
      http.get(`${API}/api/assets/tree`, () =>
        HttpResponse.json(quarantineTree),
      ),
    );

    render(wrap(<OverviewPage />));

    await waitFor(() => {
      expect(screen.getByTestId(OVERVIEW_PAGE_TEST_ID)).toHaveAttribute(
        "data-state",
        "partial",
      );
    });

    const groups = screen.getAllByTestId(OVERVIEW_GROUP_TEST_ID);
    const quarantineGroup = groups.find(
      (el) => el.getAttribute("data-status") === "quarantine",
    );
    expect(quarantineGroup).toBeTruthy();
    expect(quarantineGroup).not.toHaveAttribute("data-status", "good");

    const lamp = within(quarantineGroup!).getByTestId(LAMP_TEST_ID);
    expect(lamp).toHaveAttribute("data-quality", "quarantine");

    expect(screen.getByTestId(SHIP_STATUS_TEST_ID)).toHaveAttribute(
      "data-status",
      "quarantine",
    );
  });

  it("drill opens stub not 404", async () => {
    server.use(
      http.get(`${API}/api/assets/tree`, () =>
        HttpResponse.json(quarantineTree),
      ),
    );

    render(wrap(<OverviewPage />));

    await waitFor(() => {
      expect(screen.getAllByTestId(OVERVIEW_GROUP_TEST_ID).length).toBeGreaterThan(
        0,
      );
    });

    fireEvent.click(screen.getAllByTestId(OVERVIEW_GROUP_TEST_ID)[0]);

    const modal = await screen.findByTestId(DRILL_STUB_TEST_ID);
    expect(modal).toBeInTheDocument();
    expect(modal).toHaveTextContent(DRILL_STUB_COPY);
    expect(screen.queryByText(/404/i)).not.toBeInTheDocument();
  });

  it("empty honest copy with first_sample_ts", async () => {
    const emptyTree: AssetsTreeResponse = {
      root: {
        id: "ship",
        kind: "plant",
        name: "Ледокол",
        status: "unknown",
        children: [],
      },
      generated_at: "2026-07-26T12:00:00Z",
    };

    server.use(
      http.get(`${API}/api/assets/tree`, () => HttpResponse.json(emptyTree)),
      http.get(`${API}/api/sources/status`, () =>
        HttpResponse.json({
          items: [
            {
              ...sourcesStatusFixture.items[0],
              last_poll_ts: "2026-07-26T10:15:00.000Z",
            },
          ],
        }),
      ),
    );

    render(wrap(<OverviewPage />));

    await waitFor(() => {
      expect(screen.getByTestId(OVERVIEW_PAGE_TEST_ID)).toHaveAttribute(
        "data-state",
        "empty",
      );
    });

    const shell = screen.getByTestId(STATE_SHELL_TEST_ID);
    expect(shell).toHaveAttribute("data-variant", "empty");
    expect(shell).toHaveTextContent(/Данные собираются с/);
    expect(shell).toHaveTextContent(/10/);
    expect(shell).toHaveTextContent(/2026/);
  });
});
