import type { ReactNode } from "react";

import { AppShell } from "@/features/shell/AppShell";
import { FreshnessController } from "@/features/shell/FreshnessController";

export default function AuthenticatedLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <AppShell freshnessSlot={<FreshnessController />}>{children}</AppShell>
  );
}
