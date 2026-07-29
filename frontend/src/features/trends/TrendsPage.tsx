"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, type CSSProperties } from "react";

import { StateShell } from "@/components/ds/StateShell";
import { SelectedTags, TagPicker } from "@/components/ds/TagPicker";
import type { TagPickerItem } from "@/components/ds/TagPicker";
import { TrendChartContainer } from "@/components/ds/TrendChartContainer";
import { fetchAssetsTree } from "@/lib/api/assets";
import { queryKeys } from "@/lib/api/query-keys";
import type { AssetTreeNode } from "@/lib/api/types";
import type { ChartQualityBanner } from "@/lib/trends/chart-lib-spec";

import { journalDeepLinkFromMarker } from "./journalFromMarker";
import {
  RANGE_PRESETS,
  defaultRange,
  parseTrendsSearchParams,
  rangeFromPreset,
  serializeTrendsParams,
  type RangePreset,
  type TrendsParams,
} from "./trendsParams";
import { useEventMarkers } from "./useEventMarkers";
import { useSeries } from "./useSeries";
import { useSetpoints } from "./useSetpoints";
import { useTrendRealtime } from "./useTrendRealtime";

export const TRENDS_PAGE_TEST_ID = "trends-page";
export const EMPTY_PERIOD_COPY = "У тега нет данных за период";
export const PERIOD_TOO_LONG_COPY = "Сократите период (max 90 дней)";

function collectTagLeaves(root: AssetTreeNode): TagPickerItem[] {
  const items: TagPickerItem[] = [];

  function walk(node: AssetTreeNode): void {
    if (node.kind === "tag" && node.tag_id) {
      items.push({ id: node.tag_id, name: node.name });
      return;
    }
    for (const child of node.children ?? []) {
      walk(child);
    }
  }

  walk(root);
  return items;
}

function chartQuality(
  points: Array<{ quality: string; value: number | null }>,
  valuesStale: boolean,
): ChartQualityBanner {
  if (valuesStale) return "stale";
  const hasBad = points.some(
    (p) =>
      p.value === null ||
      p.quality === "bad" ||
      p.quality === "quarantine",
  );
  if (hasBad) return "partial";
  return "good";
}

export function TrendsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const parsed = useMemo(
    () => parseTrendsSearchParams(searchParams),
    [searchParams],
  );

  const range = useMemo(() => {
    if (parsed.from && parsed.to) {
      return { from: parsed.from, to: parsed.to };
    }
    return defaultRange(parsed.mode);
  }, [parsed.from, parsed.to, parsed.mode]);

  const replaceParams = useCallback(
    (next: TrendsParams) => {
      const qs = serializeTrendsParams(next).toString();
      router.replace(qs ? `/trends?${qs}` : "/trends");
    },
    [router],
  );

  const treeQuery = useQuery({
    queryKey: queryKeys.assetsTree,
    queryFn: async ({ signal }) => {
      const result = await fetchAssetsTree(signal);
      return result.data;
    },
    staleTime: 60_000,
    retry: false,
  });

  const catalog = useMemo(() => {
    const fromTree = treeQuery.data
      ? collectTagLeaves(treeQuery.data.root)
      : [];
    const byId = new Map(fromTree.map((t) => [t.id, t]));
    for (const tag of parsed.tags) {
      if (!byId.has(tag)) {
        byId.set(tag, { id: tag, name: tag });
      }
    }
    return Array.from(byId.values());
  }, [treeQuery.data, parsed.tags]);

  const hasWindow = Boolean(parsed.tags[0] && range.from && range.to);

  const series = useSeries(
    parsed.tags,
    range.from,
    range.to,
    hasWindow,
  );
  const setpoints = useSetpoints(parsed.tags);
  const markers = useEventMarkers(range.from, range.to, undefined, hasWindow);
  const realtime = useTrendRealtime(
    parsed.tags,
    range.from,
    range.to,
    parsed.mode,
  );

  const quality = chartQuality(series.points, realtime.valuesStale);
  const tagLabel = useMemo(() => {
    if (parsed.tags.length === 0) return undefined;
    return parsed.tags
      .map((id) => catalog.find((t) => t.id === id)?.name ?? id)
      .join(", ");
  }, [parsed.tags, catalog]);
  const isEmptyPeriod =
    hasWindow &&
    !series.isLoading &&
    !series.isError &&
    series.points.length === 0;

  const onAddTag = (tagId: string) => {
    if (parsed.tags.includes(tagId)) return;
    replaceParams({
      ...parsed,
      tags: [...parsed.tags, tagId],
      from: range.from,
      to: range.to,
    });
  };

  const onRemoveTag = (tagId: string) => {
    replaceParams({
      ...parsed,
      tags: parsed.tags.filter((t) => t !== tagId),
      from: range.from,
      to: range.to,
    });
  };

  const onMode = (mode: TrendsParams["mode"]) => {
    replaceParams({
      ...parsed,
      mode,
      from: range.from,
      to: range.to,
    });
  };

  const onPreset = (preset: RangePreset) => {
    const next = rangeFromPreset(preset);
    replaceParams({
      ...parsed,
      from: next.from,
      to: next.to,
    });
  };

  const onRangeChange = (from: string, to: string) => {
    replaceParams({
      ...parsed,
      from,
      to,
    });
  };

  const onMarkerClick = (markerId: string) => {
    const marker = markers.markers.find((m) => m.id === markerId);
    if (!marker) return;
    router.push(journalDeepLinkFromMarker(marker));
  };

  if (series.isPeriodTooLong) {
    return (
      <div data-testid={TRENDS_PAGE_TEST_ID} data-state="error-413">
        <StateShell variant="error" message={PERIOD_TOO_LONG_COPY} />
      </div>
    );
  }

  if (series.isError) {
    return (
      <div data-testid={TRENDS_PAGE_TEST_ID} data-state="error">
        <StateShell
          variant="error"
          message="Тренды недоступны"
          onRetry={series.refetch}
        />
      </div>
    );
  }

  return (
    <div
      data-testid={TRENDS_PAGE_TEST_ID}
      data-state={series.isLoading ? "loading" : isEmptyPeriod ? "empty" : "ready"}
      data-mode={parsed.mode}
      data-live={realtime.live ? "on" : "off"}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-3, 12px)",
        padding: "var(--panel-pad, 16px)",
        minHeight: "100%",
        background: "var(--surface-0)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-sans)",
      }}
    >
      <header
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "var(--space-3, 12px)",
          borderBottom: "var(--border-width, 1px) solid var(--border-subtle)",
          paddingBottom: "var(--space-2, 8px)",
        }}
      >
        <div
          role="group"
          aria-label="Режим тренда"
          style={{ display: "flex", gap: 4 }}
        >
          <button
            type="button"
            data-testid="trends-mode-quick"
            aria-pressed={parsed.mode === "quick"}
            onClick={() => onMode("quick")}
            style={modeBtnStyle(parsed.mode === "quick")}
          >
            Быстрый
          </button>
          <button
            type="button"
            data-testid="trends-mode-extended"
            aria-pressed={parsed.mode === "extended"}
            onClick={() => onMode("extended")}
            style={modeBtnStyle(parsed.mode === "extended")}
          >
            Расширенный
          </button>
        </div>

        <div style={{ flex: "1 1 220px", minWidth: 180 }}>
          <TagPicker
            tags={catalog}
            selected={parsed.tags}
            onAdd={onAddTag}
          />
        </div>

        {parsed.mode === "extended" ? (
          <button
            type="button"
            data-testid="trends-live-toggle"
            aria-pressed={realtime.live}
            onClick={() => realtime.setLive(!realtime.live)}
            style={modeBtnStyle(realtime.live)}
          >
            Live
          </button>
        ) : null}
      </header>

      <SelectedTags
        tags={catalog}
        selected={parsed.tags}
        onRemove={onRemoveTag}
      />

      {series.isLoading ? (
        <StateShell variant="loading" message="Тренды: загрузка…">
          <div
            data-testid="trends-progress"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={40}
            style={{
              height: 4,
              width: "100%",
              background: "var(--surface-2)",
              borderRadius: "var(--radius-sm, 4px)",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: "40%",
                background: "var(--accent, var(--border-strong))",
                animation: "trends-progress 1.2s ease-in-out infinite",
              }}
            />
          </div>
        </StateShell>
      ) : null}

      {isEmptyPeriod ? (
        <StateShell variant="empty" message={EMPTY_PERIOD_COPY} />
      ) : null}

      {!parsed.tags[0] && !series.isLoading ? (
        <StateShell
          variant="empty"
          message="Выберите тег для отображения тренда"
        />
      ) : null}

      {hasWindow && !isEmptyPeriod && !series.isLoading ? (
        <TrendChartContainer
          series={series.points}
          setpoints={setpoints.bands}
          markers={markers.markers}
          mode={parsed.mode}
          onRangeChange={onRangeChange}
          quality={quality}
          resolutionLabel={series.data?.resolution}
          unit={series.data?.unit}
          tagLabel={tagLabel}
          onMarkerClick={onMarkerClick}
        />
      ) : null}

      <footer
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "var(--space-2, 8px)",
          borderTop: "var(--border-width, 1px) solid var(--border-subtle)",
          paddingTop: "var(--space-2, 8px)",
        }}
      >
        <span style={{ fontSize: "var(--font-caption, 12px)", color: "var(--text-muted)" }}>
          Период
        </span>
        {RANGE_PRESETS.map((preset) => (
          <button
            key={preset}
            type="button"
            data-testid={`trends-preset-${preset}`}
            onClick={() => onPreset(preset)}
            style={modeBtnStyle(false)}
          >
            {preset}
          </button>
        ))}
        <span
          data-testid="trends-range-label"
          style={{
            marginLeft: "auto",
            fontFamily: "var(--font-mono, ui-monospace, monospace)",
            fontSize: "var(--font-caption, 12px)",
            color: "var(--text-secondary)",
          }}
        >
          {range.from} → {range.to}
        </span>
      </footer>
    </div>
  );
}

function modeBtnStyle(active: boolean): CSSProperties {
  return {
    minHeight: "var(--touch-min, 48px)",
    minWidth: "var(--touch-min, 48px)",
    padding: "0 14px",
    border: "var(--border-width, 1px) solid var(--border-strong)",
    borderRadius: "var(--radius-sm, 4px)",
    background: active ? "var(--surface-2)" : "var(--surface-1)",
    color: "var(--text-primary)",
    fontFamily: "inherit",
    fontSize: "var(--font-body, 14px)",
    cursor: "pointer",
    boxShadow: active ? "inset 0 -2px 0 var(--accent, var(--border-strong))" : "none",
  };
}
