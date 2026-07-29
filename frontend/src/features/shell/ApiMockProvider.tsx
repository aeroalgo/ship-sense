"use client";

import { useEffect, useState, type ReactNode } from "react";

import { isApiMockEnabled } from "@/lib/api/mock-flag";

export const API_MOCK_READY_TEST_ID = "api-mock-ready";

export function ApiMockProvider({ children }: { children: ReactNode }) {
  const mockOn = isApiMockEnabled();
  const [ready, setReady] = useState(!mockOn);

  useEffect(() => {
    if (!mockOn) return;

    let cancelled = false;

    async function startWorker() {
      const { worker } = await import("@/test/msw/browser");
      await worker.start({
        onUnhandledRequest: "bypass",
        quiet: true,
        serviceWorker: {
          url: "/mockServiceWorker.js",
        },
      });
      if (!cancelled) setReady(true);
    }

    void startWorker();

    return () => {
      cancelled = true;
    };
  }, [mockOn]);

  if (!ready) {
    return (
      <div
        data-testid={API_MOCK_READY_TEST_ID}
        data-ready="false"
        style={{
          minHeight: "100dvh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--surface-0, #121418)",
          color: "var(--text-secondary, #889098)",
          fontFamily: "var(--font-sans, system-ui, sans-serif)",
          fontSize: "var(--font-body, 18px)",
        }}
      >
        Подключение mock API…
      </div>
    );
  }

  return (
    <div data-testid={API_MOCK_READY_TEST_ID} data-ready="true" data-mock={mockOn ? "1" : "0"}>
      {children}
    </div>
  );
}
