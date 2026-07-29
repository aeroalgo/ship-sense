import { Suspense } from "react";

import { StateShell } from "@/components/ds/StateShell";
import { JournalPage } from "@/features/journal/JournalPage";

import "@/styles/print-journal.css";

export default function JournalRoutePage() {
  return (
    <Suspense
      fallback={<StateShell variant="loading" message="Журнал: загрузка…" />}
    >
      <JournalPage />
    </Suspense>
  );
}
