"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Lamp } from "@/components/ds/Lamp";
import { PrintLayout } from "@/components/ds/PrintLayout";
import { StateShell } from "@/components/ds/StateShell";
import { WatchSection } from "@/components/ds/WatchSection";
import { WatchVerdict } from "@/components/ds/WatchVerdict";

import { DataQualityPanel } from "./DataQualityPanel";
import { DebounceGroupRow } from "./DebounceGroupRow";
import { HandoffButton } from "./HandoffButton";
import {
  DRIFTS_STUB_COPY,
  HANDOFF_BANNER_COPY,
  HANDOFF_BANNER_MS,
  SECTION_TITLES,
  WATCH_SECTION_TEST_ID,
  defaultWatchPeriod,
  formatWatchTime,
} from "./debounce";
import { useWatchReport } from "./useWatchReport";

export const WATCH_PAGE_TEST_ID = "watch-page";
export const WATCH_HANDOFF_BANNER_TEST_ID = "watch-handoff-banner";
export const WATCH_VERDICT_CONFLICT_TEST_ID = "watch-verdict-conflict";
export const WATCH_PRINT_ROOT_TEST_ID = "watch-print-root";

function parsePeriod(search: URLSearchParams): { from: string; to: string } {
  const from = search.get("from");
  const to = search.get("to");
  if (from && to) {
    return { from, to };
  }
  return defaultWatchPeriod();
}

export function WatchPage() {
  const searchParams = useSearchParams();
  const period = useMemo(() => parsePeriod(searchParams), [searchParams]);
  const query = useWatchReport(period.from, period.to);
  const [bannerVisible, setBannerVisible] = useState(true);
  const [printOpen, setPrintOpen] = useState(false);

  useEffect(() => {
    setBannerVisible(true);
    const id = window.setTimeout(() => {
      setBannerVisible(false);
    }, HANDOFF_BANNER_MS);
    return () => window.clearTimeout(id);
  }, [period.from, period.to]);

  if (query.isLoading) {
    return (
      <div data-testid={WATCH_PAGE_TEST_ID} data-state="loading">
        <StateShell variant="loading" message="Вахтенный: загрузка…" />
      </div>
    );
  }

  if (query.isError || !query.data) {
    return (
      <div data-testid={WATCH_PAGE_TEST_ID} data-state="error">
        <StateShell
          variant="error"
          message="Не удалось загрузить вахтенную сводку"
        />
      </div>
    );
  }

  const view = query.data;
  const { report, protections, alarmGroups, verdict } = view;
  const protectionLabels = protections.map((event) => ({
    id: event.id,
    label: `${formatWatchTime(event.ts)} - ${event.event_name}`,
  }));

  const provenance = [
    `Вахтенный: ${report.watchkeeper.name} (${report.watchkeeper.rank})`,
    `Период: ${report.period.from} → ${report.period.to}`,
    `Сформировано: ${report.generated_at}`,
  ].join(" · ");

  return (
    <div
      data-testid={WATCH_PAGE_TEST_ID}
      data-state="ready"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 16,
        padding: "var(--panel-pad, 16px)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-sans)",
        background: "var(--surface-0)",
        minHeight: "100%",
      }}
    >
      {bannerVisible ? (
        <div
          data-testid={WATCH_HANDOFF_BANNER_TEST_ID}
          role="status"
          style={{
            padding: "12px var(--panel-pad, 16px)",
            minHeight: "var(--touch-min, 48px)",
            display: "flex",
            alignItems: "center",
            background: "var(--surface-1)",
            border: "var(--border-width, 1px) solid var(--border-subtle)",
            borderLeft: "4px solid var(--text-secondary)",
            fontSize: "var(--font-body)",
            fontWeight: 600,
          }}
        >
          {HANDOFF_BANNER_COPY}
        </div>
      ) : null}

      <WatchVerdict text={verdict.text} tone={verdict.tone} />

      {view.verdictConflict ? (
        <div
          data-testid={WATCH_VERDICT_CONFLICT_TEST_ID}
          role="alert"
          style={{
            padding: "12px var(--panel-pad, 16px)",
            background: "var(--surface-1)",
            borderLeft: "4px solid var(--alarm-warning-fg)",
            color: "var(--alarm-warning-fg)",
            fontSize: "var(--font-caption, 0.875rem)",
          }}
        >
          Вердикт API расходится со счётчиками. Клиент: {view.clientVerdictText}
        </div>
      ) : null}

      <div data-watch-section="protections" data-testid={`${WATCH_SECTION_TEST_ID}-protections`}>
        <WatchSection
          title={SECTION_TITLES.protections}
          items={[]}
          collapsible={false}
          defaultOpen
        >
          {protections.length === 0 ? (
            <li
              style={{
                listStyle: "none",
                padding: "8px 0",
                color: "var(--text-secondary)",
              }}
            >
              Защит за период не было
            </li>
          ) : (
            protections.map((event) => (
              <li
                key={event.id}
                data-protection-id={event.id}
                style={{
                  listStyle: "none",
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  minHeight: 40,
                  padding: "6px 0",
                  borderTop:
                    "var(--border-width, 1px) solid var(--border-subtle)",
                  fontFamily: "var(--font-mono, var(--font-sans))",
                }}
              >
                <Lamp
                  severity="protection-shutdown"
                  lifecycle="active"
                  quality="good"
                  size="sm"
                />
                <span>
                  {formatWatchTime(event.ts)} - {event.event_name}
                </span>
              </li>
            ))
          )}
        </WatchSection>
      </div>

      <div data-watch-section="alarms" data-testid={`${WATCH_SECTION_TEST_ID}-alarms`}>
        <WatchSection
          title={SECTION_TITLES.alarms}
          items={[]}
          collapsible
          defaultOpen
        >
          {alarmGroups.length === 0 ? (
            <li
              style={{
                listStyle: "none",
                padding: "8px 0",
                color: "var(--text-secondary)",
              }}
            >
              Нет тревог за период
            </li>
          ) : (
            alarmGroups.map((group) => (
              <DebounceGroupRow
                key={group.key}
                group={group}
                memberTimestamps={view.memberTimestamps}
              />
            ))
          )}
        </WatchSection>
      </div>

      <div data-watch-section="drifts" data-testid={`${WATCH_SECTION_TEST_ID}-drifts`}>
        <WatchSection
          title={SECTION_TITLES.drifts}
          items={[{ id: "drifts-stub", label: DRIFTS_STUB_COPY }]}
          collapsible
          defaultOpen
        />
      </div>

      <DataQualityPanel
        quarantine_tags={report.data_quality.quarantine_tags}
        stale_intervals={report.data_quality.stale_intervals}
        banner={report.data_quality.banner}
      />

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 12,
          paddingTop: 8,
          alignItems: "center",
        }}
      >
        <button
          type="button"
          onClick={() => setPrintOpen((v) => !v)}
          style={{
            minHeight: "var(--touch-min, 48px)",
            minWidth: "var(--touch-min, 48px)",
            padding: "0 16px",
            border: "var(--border-width, 1px) solid var(--border-subtle)",
            background: "var(--surface-1)",
            color: "var(--text-primary)",
            fontFamily: "inherit",
            fontSize: "var(--font-body)",
            cursor: "pointer",
          }}
        >
          Печать
        </button>
        <HandoffButton />
      </div>

      {printOpen ? (
        <div data-testid={WATCH_PRINT_ROOT_TEST_ID}>
          <PrintLayout title="Вахтенная сводка" provenance={provenance}>
            <WatchVerdict text={verdict.text} tone={verdict.tone} />
            <section style={{ marginTop: 16 }}>
              <h2 style={{ fontSize: "var(--font-body)" }}>
                {SECTION_TITLES.protections}
              </h2>
              <ul>
                {protectionLabels.map((item) => (
                  <li key={item.id}>{item.label}</li>
                ))}
              </ul>
            </section>
            <section style={{ marginTop: 16 }}>
              <h2 style={{ fontSize: "var(--font-body)" }}>
                {SECTION_TITLES.alarms}
              </h2>
              <ul>
                {alarmGroups.map((group) => (
                  <li key={group.key}>
                    {formatWatchTime(group.first_ts)} - {group.event_name}
                    {group.collapsed ? ` (×${group.count} дребезг)` : ""}
                    {group.collapsed ? (
                      <details open>
                        <summary>
                          {group.count} срабатываний; детали в журнале
                        </summary>
                        <ul>
                          {group.member_ids.map((id) => (
                            <li key={id}>
                              {view.memberTimestamps[id]
                                ? formatWatchTime(view.memberTimestamps[id])
                                : id}
                            </li>
                          ))}
                        </ul>
                      </details>
                    ) : null}
                  </li>
                ))}
              </ul>
            </section>
            <div style={{ marginTop: 16 }}>
              <DataQualityPanel
                quarantine_tags={report.data_quality.quarantine_tags}
                stale_intervals={report.data_quality.stale_intervals}
                banner={report.data_quality.banner}
              />
            </div>
          </PrintLayout>
        </div>
      ) : null}
    </div>
  );
}
