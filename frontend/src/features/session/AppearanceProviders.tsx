"use client";

import type { ReactNode } from "react";

import { ApiMockProvider } from "@/features/shell/ApiMockProvider";

import { DesignProvider } from "./DesignProvider";
import { SessionProvider } from "./useSession";
import { ThemeProvider } from "./ThemeProvider";

export function AppearanceProviders({ children }: { children: ReactNode }) {
  return (
    <ApiMockProvider>
      <ThemeProvider>
        <DesignProvider>
          <SessionProvider>{children}</SessionProvider>
        </DesignProvider>
      </ThemeProvider>
    </ApiMockProvider>
  );
}
