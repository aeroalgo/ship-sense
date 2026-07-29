import { Suspense } from "react";

import { StateShell } from "@/components/ds/StateShell";
import { WatchPage } from "@/features/watch/WatchPage";

export default function WatchRoutePage() {
  return (
    <Suspense
      fallback={<StateShell variant="loading" message="Вахтенный: загрузка…" />}
    >
      <WatchPage />
    </Suspense>
  );
}
