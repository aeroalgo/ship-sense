export type LampSeverity =
  | "norm"
  | "warning-drift"
  | "alarm"
  | "protection-shutdown"
  | "no-data"
  | "info";

export type LampLifecycle = "active" | "acked" | "cleared";

export type LampQuality =
  | "good"
  | "uncertain"
  | "bad"
  | "stale"
  | "quarantine";

export type LampSize = "sm" | "md" | "lg" | "xl";

export type LampProps = {
  severity: LampSeverity;
  lifecycle: LampLifecycle;
  quality: LampQuality;
  size?: LampSize;
  /** Q4 mode A: lifecycle derived from reconstruction — show legend, not trust as APS ack */
  reconstructed?: boolean;
};

export const LAMP_TEST_ID = "lamp";

export const LAMP_SEVERITIES: readonly LampSeverity[] = [
  "norm",
  "warning-drift",
  "alarm",
  "protection-shutdown",
  "no-data",
  "info",
] as const;

export const LAMP_LIFECYCLES: readonly LampLifecycle[] = [
  "active",
  "acked",
  "cleared",
] as const;

export const LAMP_QUALITIES: readonly LampQuality[] = [
  "good",
  "uncertain",
  "bad",
  "stale",
  "quarantine",
] as const;

export const LAMP_SIZE_PX: Record<LampSize, number> = {
  sm: 16,
  md: 24,
  lg: 32,
  xl: 48,
};

/** Public SVG paths (Next.js `public/`). */
export const SEVERITY_SVG: Record<LampSeverity, string> = {
  norm: "/ds/lamps/severity-norm.svg",
  "warning-drift": "/ds/lamps/severity-warning.svg",
  alarm: "/ds/lamps/severity-alarm.svg",
  "protection-shutdown": "/ds/lamps/severity-protection.svg",
  "no-data": "/ds/lamps/severity-no-data.svg",
  info: "/ds/lamps/severity-info.svg",
};

export const QUALITY_OVERLAY_SVG: Partial<Record<LampQuality, string>> = {
  uncertain: "/ds/lamps/overlay-uncertain.svg",
  bad: "/ds/lamps/overlay-bad.svg",
  stale: "/ds/lamps/overlay-stale.svg",
  quarantine: "/ds/lamps/overlay-quarantine.svg",
};

/** CSS color token for severity layer (currentColor / mask). */
export const SEVERITY_COLOR_TOKEN: Record<LampSeverity, string> = {
  norm: "var(--text-muted)",
  "warning-drift": "var(--alarm-warning-fg)",
  alarm: "var(--alarm-critical-fg)",
  "protection-shutdown": "var(--alarm-critical-fg)",
  "no-data": "var(--text-secondary)",
  info: "var(--alarm-info-fg)",
};

export const QUALITY_COLOR_TOKEN: Record<LampQuality, string | null> = {
  good: null,
  uncertain: "var(--quality-uncertain-fg)",
  bad: "var(--quality-bad-fg)",
  stale: "var(--quality-stale-fg)",
  quarantine: "var(--quality-quarantine-fg)",
};

/** Pulse only active + unacked critical severities. */
export function shouldPulse(
  severity: LampSeverity,
  lifecycle: LampLifecycle,
): boolean {
  if (lifecycle !== "active") return false;
  return severity === "alarm" || severity === "protection-shutdown";
}

/**
 * AggregateShipStatus / OverviewGroupCard: map rollup quality + worst event severity.
 * quarantine / unknown / no-data never render as green norm.
 */
export function resolveGroupLamp(input: {
  aggregateQuality: LampQuality | "unknown";
  worstSeverity: LampSeverity | null;
  lifecycle?: LampLifecycle;
}): Pick<LampProps, "severity" | "quality" | "lifecycle"> {
  const lifecycle = input.lifecycle ?? "active";

  if (input.aggregateQuality === "unknown") {
    return { severity: "no-data", quality: "good", lifecycle };
  }

  if (input.aggregateQuality === "quarantine") {
    return {
      severity: input.worstSeverity ?? "norm",
      quality: "quarantine",
      lifecycle,
    };
  }

  if (
    input.aggregateQuality === "stale" ||
    input.aggregateQuality === "bad" ||
    input.aggregateQuality === "uncertain"
  ) {
    return {
      severity: input.worstSeverity ?? "norm",
      quality: input.aggregateQuality,
      lifecycle,
    };
  }

  if (input.worstSeverity && input.worstSeverity !== "norm") {
    return {
      severity: input.worstSeverity,
      quality: "good",
      lifecycle,
    };
  }

  return { severity: "norm", quality: "good", lifecycle };
}

export const LIFECYCLE_OPACITY: Record<LampLifecycle, number> = {
  active: 1,
  acked: 0.55,
  cleared: 0.4,
};

/** 0.5 Hz outline pulse — period 2000ms. Honours prefers-reduced-motion → static. */
export const LAMP_PULSE = {
  hz: 0.5,
  periodMs: 2000,
  cssVar: "--lamp-pulse-ms",
} as const;

export const GRAYSCALE_PROOF_PATH = "/ds/lamps/grayscale-proof.html";
