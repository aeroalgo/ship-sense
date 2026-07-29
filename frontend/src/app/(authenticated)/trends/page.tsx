import { Suspense } from "react";

import { StateShell } from "@/components/ds/StateShell";
import { TrendsPage } from "@/features/trends/TrendsPage";

export default function TrendsRoutePage() {
  return (
    <Suspense
      fallback={<StateShell variant="loading" message="Тренды: загрузка…" />}
    >
      <TrendsPage />
    </Suspense>
  );
}
