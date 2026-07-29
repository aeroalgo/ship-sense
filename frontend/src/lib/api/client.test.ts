import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { ApiError, apiGet, joinApiUrl } from "./client";
import { fetchAssetsTree } from "./assets";
import { fetchEvents } from "./events";
import { handlers } from "@/test/msw/handlers";

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  server.resetHandlers();
  delete process.env.NEXT_PUBLIC_API_URL;
});
afterAll(() => server.close());

describe("joinApiUrl", () => {
  it("joins base without trailing slash and absolute path", () => {
    expect(joinApiUrl("http://localhost:8000", "/api/assets/tree")).toBe(
      "http://localhost:8000/api/assets/tree",
    );
  });

  it("strips trailing slash on base and leading slash on path variants", () => {
    expect(joinApiUrl("http://localhost:8000/", "api/assets/tree")).toBe(
      "http://localhost:8000/api/assets/tree",
    );
  });
});

describe("apiGet error shape", () => {
  it("maps 401 envelope to ApiError with code/message", async () => {
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
    server.use(
      http.get("http://localhost:8000/api/session-probe", () =>
        HttpResponse.json(
          {
            error: {
              code: "UNAUTHORIZED",
              message: "Session required",
              details: { reason: "missing_cookie" },
            },
          },
          { status: 401 },
        ),
      ),
    );

    await expect(apiGet("/api/session-probe")).rejects.toSatisfy(
      (err: unknown) => {
        expect(err).toBeInstanceOf(ApiError);
        const e = err as ApiError;
        expect(e.status).toBe(401);
        expect(e.code).toBe("UNAUTHORIZED");
        expect(e.message).toBe("Session required");
        expect(e.details).toEqual({ reason: "missing_cookie" });
        return true;
      },
    );
  });
});

describe("MSW happy path — assets.tree", () => {
  it("fetchAssetsTree returns typed tree from MSW fixture", async () => {
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
    const { data } = await fetchAssetsTree();
    expect(data.root.id).toBe("ship");
    expect(data.root.kind).toBe("plant");
    expect(data.root.children?.length).toBeGreaterThan(0);
    expect(data.generated_at).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });
});

describe("MSW — events reconstruction header", () => {
  it("fetchEvents exposes X-Events-Reconstruction", async () => {
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
    const result = await fetchEvents({ limit: 20 });
    expect(result.reconstruction).toBe("edge_only");
    expect(result.data.items.length).toBeGreaterThan(0);
  });
});
