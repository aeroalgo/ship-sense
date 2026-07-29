import { http, HttpResponse } from "msw";
import { EVENTS_RECONSTRUCTION_HEADER } from "@/lib/api/types";
import {
  assetsTreeFixture,
  eventsListFixture,
  reportsListFixture,
  rosterFixture,
  seriesFixture,
  sessionFixture,
  setpointHistoryFixture,
  setpointsFixture,
  sourcesStatusFixture,
  watchReportFixture,
} from "./fixtures";

export const handlers = [
  http.get("*/api/assets/tree", () => HttpResponse.json(assetsTreeFixture)),

  http.get("*/api/events", () =>
    HttpResponse.json(eventsListFixture, {
      headers: {
        [EVENTS_RECONSTRUCTION_HEADER]: "edge_only",
        "Access-Control-Expose-Headers": EVENTS_RECONSTRUCTION_HEADER,
      },
    }),
  ),

  http.get("*/api/series", () => HttpResponse.json(seriesFixture)),

  http.get("*/api/series/aggregate", () =>
    HttpResponse.json({
      from: "2026-07-26T00:00:00Z",
      to: "2026-07-26T12:00:00Z",
      resolution: "5m",
      series: [
        {
          tag_id: seriesFixture.tag_id,
          unit: seriesFixture.unit,
          points: seriesFixture.points,
        },
      ],
    }),
  ),

  http.get("*/api/setpoints", () => HttpResponse.json(setpointsFixture)),

  http.get("*/api/setpoints/history", () =>
    HttpResponse.json(setpointHistoryFixture),
  ),

  http.get("*/api/reports", () => HttpResponse.json(reportsListFixture)),

  http.get("*/api/reports/watch", ({ request }) => {
    const format = new URL(request.url).searchParams.get("format") ?? "json";
    if (format === "html") {
      return new HttpResponse("<html><body>watch report</body></html>", {
        headers: { "Content-Type": "text/html; charset=utf-8" },
      });
    }
    return HttpResponse.json(watchReportFixture);
  }),

  http.get("*/api/watch/roster", () => HttpResponse.json(rosterFixture)),

  http.post("*/api/session", async ({ request }) => {
    const body = (await request.json()) as { person_id?: string };
    if (!body.person_id) {
      return HttpResponse.json(
        {
          error: {
            code: "VALIDATION_ERROR",
            message: "person_id required",
          },
        },
        { status: 400 },
      );
    }
    const person = rosterFixture.items.find((p) => p.person_id === body.person_id);
    if (!person) {
      return HttpResponse.json(
        {
          error: {
            code: "NOT_FOUND",
            message: "person not in roster",
          },
        },
        { status: 404 },
      );
    }
    return HttpResponse.json(
      {
        ...sessionFixture,
        person_id: person.person_id,
        name: person.name,
        rank: person.rank,
        default_screen: person.default_screen,
      },
      {
        status: 201,
        headers: {
          "Set-Cookie":
            "shipsense_session=mock-session; HttpOnly; SameSite=Lax; Path=/",
        },
      },
    );
  }),

  http.delete("*/api/session", () => new HttpResponse(null, { status: 204 })),

  http.get("*/api/sources/status", () =>
    HttpResponse.json(sourcesStatusFixture),
  ),
];
