"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { AggregateShipStatus } from "@/components/ds/AggregateShipStatus";
import { QuarantineBanner } from "@/components/ds/QuarantineBanner";
import { StateShell } from "@/components/ds/StateShell";
import { fetchSourcesStatus } from "@/lib/api/sources";
import { queryKeys } from "@/lib/api/query-keys";
import type { AssetTreeNode } from "@/lib/api/types";

import { DrillDownStubModal } from "./DrillDownStubModal";
import { MoSection } from "./MoSection";
import {
  collectQuarantineTagIds,
  flattenTagIds,
  hasOverviewData,
  partitionMoSections,
  shipStatusLabel,
} from "./treeUtils";
import { useAssetsTree } from "./useAssetsTree";
import { useOverviewRealtime } from "./useOverviewRealtime";

export const OVERVIEW_PAGE_TEST_ID = "overview-page";

function formatFirstSampleTs(iso: string): string {
  try {
    return new Date(iso).toLocaleString("ru-RU", { timeZone: "UTC" }) + " UTC";
  } catch {
    return iso;
  }
}

function earliestSourceTs(
  items: Array<{ last_poll_ts: string }>,
): string | null {
  if (items.length === 0) return null;
  let earliest = items[0].last_poll_ts;
  for (let i = 1; i < items.length; i += 1) {
    if (items[i].last_poll_ts < earliest) {
      earliest = items[i].last_poll_ts;
    }
  }
  return earliest;
}

export function OverviewPage() {
  const { tree, isLoading, isError, refetch } = useAssetsTree();
  const sources = useQuery({
    queryKey: queryKeys.sourcesStatus,
    queryFn: async ({ signal }) => {
      const result = await fetchSourcesStatus(signal);
      return result.data;
    },
    staleTime: 30_000,
    retry: false,
  });

  const tagIds = useMemo(
    () => (tree ? flattenTagIds(tree.root) : []),
    [tree],
  );
  const { valuesStale } = useOverviewRealtime(
    tagIds,
    Boolean(tree && hasOverviewData(tree)),
  );

  const [drillGroup, setDrillGroup] = useState<AssetTreeNode | null>(null);

  const quarantineTags = useMemo(
    () => (tree ? collectQuarantineTagIds(tree.root) : []),
    [tree],
  );

  const sections = useMemo(
    () => (tree ? partitionMoSections(tree.root) : { nos: [], stern: [] }),
    [tree],
  );

  const firstSampleTs =
    earliestSourceTs(sources.data?.items ?? []) ?? tree?.generated_at ?? null;

  if (isLoading) {
    return (
      <div data-testid={OVERVIEW_PAGE_TEST_ID} data-state="loading">
        <StateShell variant="loading" message="Обзор: загрузка…" />
        <div
          aria-hidden
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "var(--space-4, 16px)",
            padding: "var(--panel-pad, 16px)",
          }}
        >
          {Array.from({ length: 8 }).map((_, index) => (
            <div
              key={index}
              style={{
                minHeight: 120,
                background: "var(--surface-2)",
                borderRadius: "var(--radius-md)",
                opacity: 0.6,
              }}
            />
          ))}
        </div>
      </div>
    );
  }

  if (isError || !tree) {
    return (
      <div data-testid={OVERVIEW_PAGE_TEST_ID} data-state="error">
        <StateShell
          variant="error"
          message="Дерево активов недоступно"
          onRetry={refetch}
        />
      </div>
    );
  }

  if (!hasOverviewData(tree)) {
    const ts = firstSampleTs
      ? formatFirstSampleTs(firstSampleTs)
      : "-";
    return (
      <div data-testid={OVERVIEW_PAGE_TEST_ID} data-state="empty">
        <StateShell
          variant="empty"
          message={`Данные собираются с ${ts}`}
        />
      </div>
    );
  }

  const shipStatus = tree.root.status;
  const partial = quarantineTags.length > 0;
  const stale = valuesStale || shipStatus === "stale";

  return (
    <div
      data-testid={OVERVIEW_PAGE_TEST_ID}
      data-state={stale ? "stale" : partial ? "partial" : "ready"}
      data-stale={stale ? "true" : "false"}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-4, 16px)",
        padding: "var(--panel-pad, 16px)",
      }}
    >
      {partial ? (
        <QuarantineBanner tags={quarantineTags} scope="обзор" />
      ) : null}

      <AggregateShipStatus
        status={shipStatus}
        label={shipStatusLabel(shipStatus)}
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "var(--space-4, 16px)",
        }}
      >
        <MoSection
          section="nos"
          title="НОС"
          groups={sections.nos}
          onGroupClick={setDrillGroup}
        />
        <MoSection
          section="stern"
          title="КОРМА"
          groups={sections.stern}
          onGroupClick={setDrillGroup}
        />
      </div>

      <DrillDownStubModal
        open={drillGroup !== null}
        groupName={drillGroup?.name ?? null}
        onClose={() => setDrillGroup(null)}
      />
    </div>
  );
}
