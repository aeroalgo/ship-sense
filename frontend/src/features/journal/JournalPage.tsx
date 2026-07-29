"use client";

import { useVirtualizer } from "@tanstack/react-virtual";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useRef } from "react";

import { EventFilters } from "@/components/ds/EventFilters";
import type { EventFiltersValue } from "@/components/ds/EventFilters";
import { EventRow } from "@/components/ds/EventRow";
import { PrintLayout } from "@/components/ds/PrintLayout";
import { QuarantineBanner } from "@/components/ds/QuarantineBanner";
import { StateShell } from "@/components/ds/StateShell";
import { queryKeys } from "@/lib/api/query-keys";
import { fetchSourcesStatus } from "@/lib/api/sources";
import type { EventItem } from "@/lib/api/types";
import { trendsDeepLink } from "@/lib/routing/trendsDeepLink";

import { ReconstructionBanner } from "./ReconstructionBanner";
import { SessionEventFilter } from "./SessionEventFilter";
import {
  filtersFromSearchParams,
  searchParamsFromFilters,
  type JournalFiltersValue,
} from "./journalFilters";
import { useEventsInfinite } from "./useEventsInfinite";
import { useEventsRealtime } from "./useEventsRealtime";
import { isActiveUnacked } from "./journalSort";

export const JOURNAL_PAGE_TEST_ID = "journal-page";
export const APS_ACK_FOOTNOTE =
  "Квитируется на панели АПС";

const ROW_ESTIMATE = 56;

function buildProvenance(
  sources: Array<{ name: string; tags_quarantine: number }> | undefined,
): string {
  if (!sources || sources.length === 0) {
    return "Достоверность: источники не загружены";
  }
  const names = sources.map((s) => s.name).join(", ");
  const quarantine = sources.reduce((sum, s) => sum + s.tags_quarantine, 0);
  return `Достоверность: источники ${names}; quarantine tags: ${quarantine}`;
}

export function JournalPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const filters = useMemo(
    () => filtersFromSearchParams(searchParams),
    [searchParams],
  );

  const {
    events: rawEvents,
    isLoading,
    isError,
    hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
    refetch,
    reconstruction,
  } = useEventsInfinite(filters);

  const events = useMemo(() => {
    let list = rawEvents;
    if (filters.active) {
      list = list.filter(isActiveUnacked);
    }
    if (filters.sessionAudit) {
      list = list.filter((event) =>
        event.event_name === "session_started" ||
        event.event_name === "session_ended",
      );
    }
    return list;
  }, [rawEvents, filters.active, filters.sessionAudit]);

  useEventsRealtime(filters, !isLoading && !isError);

  const sources = useQuery({
    queryKey: queryKeys.sourcesStatus,
    queryFn: async ({ signal }) => {
      const result = await fetchSourcesStatus(signal);
      return result.data;
    },
    staleTime: 30_000,
    retry: false,
  });

  const parentRef = useRef<HTMLDivElement>(null);
  const virtualizer = useVirtualizer({
    count: events.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_ESTIMATE,
    overscan: 8,
  });

  const quarantineTags = useMemo(() => {
    const tags: string[] = [];
    for (const item of sources.data?.items ?? []) {
      if (item.tags_quarantine > 0) {
        tags.push(item.name);
      }
    }
    return tags;
  }, [sources.data]);

  const provenance = buildProvenance(sources.data?.items);

  const onFiltersChange = (next: EventFiltersValue) => {
    const merged: JournalFiltersValue = {
      ...next,
      active: filters.active,
      sessionAudit: filters.sessionAudit,
      source: filters.sessionAudit ? next.source ?? "edge" : next.source,
    };
    const params = searchParamsFromFilters(merged);
    const qs = params.toString();
    router.replace(qs ? `/journal?${qs}` : "/journal");
  };

  const onSessionAuditToggle = () => {
    const enabling = !filters.sessionAudit;
    const next: JournalFiltersValue = {
      ...filters,
      sessionAudit: enabling,
      source: enabling ? "edge" : undefined,
    };
    const params = searchParamsFromFilters(next);
    const qs = params.toString();
    router.replace(qs ? `/journal?${qs}` : "/journal");
  };

  const onTrendClick = (event: EventItem) => {
    const href = trendsDeepLink(event);
    if (href) router.push(href);
  };

  const onPrint = () => {
    window.print();
  };

  if (isError) {
    return (
      <div data-testid={JOURNAL_PAGE_TEST_ID} data-state="error">
        <StateShell
          variant="error"
          message="Журнал недоступен"
          onRetry={refetch}
        />
      </div>
    );
  }

  return (
    <div
      data-testid={JOURNAL_PAGE_TEST_ID}
      data-state={isLoading ? "loading" : events.length === 0 ? "empty" : "ready"}
      className="journal-page"
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100%",
        background: "var(--surface-0)",
      }}
    >
      <div data-print-hide="true">
        <EventFilters
          filters={filters}
          onChange={onFiltersChange}
          onPrint={onPrint}
        />
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
            padding: "0 var(--panel-pad, 16px) 12px",
            alignItems: "center",
          }}
        >
          <SessionEventFilter
            active={Boolean(filters.sessionAudit)}
            onToggle={onSessionAuditToggle}
          />
          {filters.active ? (
            <span
              data-testid="journal-active-chip"
              style={{
                minHeight: "var(--touch-min, 48px)",
                display: "inline-flex",
                alignItems: "center",
                padding: "0 14px",
                border: "var(--border-width, 1px) solid var(--border-subtle)",
                borderLeft: "4px solid var(--alarm-alarm-fg, var(--text-primary))",
                background: "var(--surface-1)",
                color: "var(--text-primary)",
                fontFamily: "var(--font-sans)",
                fontSize: "var(--font-body)",
                fontWeight: 600,
              }}
            >
              Активные
            </span>
          ) : null}
        </div>
      </div>

      {reconstruction ? (
        <ReconstructionBanner mode={reconstruction} />
      ) : null}

      {quarantineTags.length > 0 ? (
        <div data-print-hide="true">
          <QuarantineBanner tags={quarantineTags} scope="журнал" />
        </div>
      ) : null}

      <p
        data-testid="aps-ack-footnote"
        style={{
          margin: 0,
          padding: "8px var(--panel-pad, 16px)",
          color: "var(--text-secondary)",
          fontSize: "var(--font-caption, 0.875rem)",
          fontFamily: "var(--font-sans)",
          borderBottom: "var(--border-width, 1px) solid var(--border-subtle)",
        }}
      >
        {APS_ACK_FOOTNOTE}
      </p>

      {isLoading ? (
        <div data-print-hide="true" aria-busy="true">
          <StateShell variant="loading" message="Журнал: загрузка…" />
          {Array.from({ length: 12 }).map((_, index) => (
            <div
              key={index}
              style={{
                height: ROW_ESTIMATE,
                margin: "0 var(--panel-pad, 16px) 4px",
                background: "var(--surface-2)",
                opacity: 0.55,
                borderRadius: "var(--radius-sm)",
              }}
            />
          ))}
        </div>
      ) : null}

      {!isLoading && events.length === 0 ? (
        <StateShell
          variant="empty"
          message="За выбранный период событий нет"
        />
      ) : null}

      {!isLoading && events.length > 0 ? (
        <>
          <div
            ref={parentRef}
            data-testid="journal-virtual-list"
            data-print-hide="true"
            style={{
              flex: 1,
              height: "calc(100vh - 220px)",
              overflow: "auto",
            }}
            onScroll={() => {
              const el = parentRef.current;
              if (!el || !hasNextPage || isFetchingNextPage) return;
              if (el.scrollTop + el.clientHeight >= el.scrollHeight - 120) {
                fetchNextPage();
              }
            }}
          >
            <div
              style={{
                height: virtualizer.getTotalSize(),
                width: "100%",
                position: "relative",
              }}
            >
              {virtualizer.getVirtualItems().map((row) => {
                const event = events[row.index];
                return (
                  <div
                    key={event.id}
                    data-index={row.index}
                    ref={virtualizer.measureElement}
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      width: "100%",
                      transform: `translateY(${row.start}px)`,
                    }}
                  >
                    <EventRow event={event} onTrendClick={onTrendClick} />
                  </div>
                );
              })}
            </div>
          </div>

          <div className="journal-print-only" hidden>
            <PrintLayout title="Журнал событий" provenance={provenance}>
              {events.map((event) => (
                <EventRow key={`print-${event.id}`} event={event} />
              ))}
            </PrintLayout>
          </div>
        </>
      ) : null}
    </div>
  );
}
