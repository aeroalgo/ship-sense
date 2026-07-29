"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import "uplot/dist/uPlot.min.css";

import {
  CHART_LIB,
  TREND_CHART_TEST_ID,
  type TrendChartProps,
} from "@/lib/trends/chart-lib-spec";
import {
  countGaps,
  createUplotAdapter,
  type UplotAdapterHandle,
} from "@/features/trends/chart/adapters/uplotAdapter";
import {
  isCanvasSafeColor,
  resolveChartTokens,
} from "@/features/trends/chart/adapters/resolveChartTokens";

import styles from "./TrendChartContainer.module.css";

export type TrendChartContainerProps = TrendChartProps;

function qualityLabel(q: TrendChartProps["quality"]): string {
  if (q === "partial") return "частично";
  if (q === "stale") return "устарело";
  return "норма";
}

export function TrendChartContainer({
  series,
  setpoints,
  markers,
  mode,
  onRangeChange,
  quality,
  resolutionLabel,
  unit,
  tagLabel,
  onMarkerClick,
}: TrendChartContainerProps) {
  const plotRef = useRef<HTMLDivElement>(null);
  const adapterRef = useRef<UplotAdapterHandle | null>(null);
  const onRangeChangeRef = useRef(onRangeChange);
  const onMarkerClickRef = useRef(onMarkerClick);
  onRangeChangeRef.current = onRangeChange;
  onMarkerClickRef.current = onMarkerClick;
  const [seriesStroke, setSeriesStroke] = useState<string | null>(null);

  const gapCount = useMemo(() => countGaps(series), [series]);

  const ariaLabel = useMemo(() => {
    const tag = tagLabel ?? "тренд";
    return `${tag}: ${series.length} точек, ${gapCount} разрывов, ${setpoints.length} уставок, ${markers.length} маркеров`;
  }, [tagLabel, series.length, gapCount, setpoints.length, markers.length]);

  useEffect(() => {
    const el = plotRef.current;
    if (!el) {
      return;
    }

    const tokens = resolveChartTokens(el);
    if (!isCanvasSafeColor(tokens.seriesStroke)) {
      tokens.seriesStroke = "#6b9fd4";
    }
    setSeriesStroke(tokens.seriesStroke);

    const adapter = createUplotAdapter(el, {
      series,
      setpoints,
      markers,
      mode,
      tokens,
      onRangeChange: (from, to) => onRangeChangeRef.current(from, to),
      onMarkerClick: (id) => onMarkerClickRef.current?.(id),
    });
    adapterRef.current = adapter;

    return () => {
      adapter.destroy();
      adapterRef.current = null;
    };
  }, [series, setpoints, markers, mode]);

  return (
    <section
      className={styles.root}
      data-testid={TREND_CHART_TEST_ID}
      data-chart-lib={CHART_LIB}
      data-mode={mode}
      data-gap-count={gapCount}
      data-setpoint-count={setpoints.length}
      data-marker-count={markers.length}
      data-series-stroke={seriesStroke ?? undefined}
      aria-label={ariaLabel}
    >
      <header className={styles.chrome}>
        {tagLabel ? <span className={styles.tag}>{tagLabel}</span> : null}
        {unit ? <span className={styles.unit}>{unit}</span> : null}
        {resolutionLabel ? (
          <span className={styles.badge}>агрегация {resolutionLabel}</span>
        ) : null}
        <span className={styles.quality} data-quality={quality}>
          {qualityLabel(quality)}
        </span>
      </header>

      <div ref={plotRef} className={styles.plot} data-testid="trend-chart-plot" />

      <footer className={styles.footer}>
        <div
          className={styles.setpoints}
          data-testid="trend-chart-setpoints"
          aria-label="Уставки"
        >
          {setpoints.map((band) => (
            <span
              key={band.id}
              className={styles.setpoint}
              data-testid="setpoint-line"
              data-setpoint-id={band.id}
              data-kind={band.kind}
            >
              {band.label}={band.value}
            </span>
          ))}
        </div>

        {markers.length > 0 ? (
          <div className={styles.markers} data-testid="trend-chart-markers">
            {markers.map((marker) => (
              <button
                key={marker.id}
                type="button"
                className={styles.markerBtn}
                data-testid="event-marker"
                data-marker-id={marker.id}
                data-marker-ts={marker.ts}
                data-severity={marker.severity}
                onClick={() => onMarkerClick?.(marker.id)}
              >
                {marker.event_name}
              </button>
            ))}
          </div>
        ) : null}

        <span className={styles.srOnly}>
          Режим {mode}. Библиотека {CHART_LIB}.
        </span>
      </footer>
    </section>
  );
}
