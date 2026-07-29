export const THEME_IDS = ["day", "night", "dim"] as const;
export type ThemeId = (typeof THEME_IDS)[number];

export const DESIGN_IDS = ["d01", "d02", "d03", "d04", "d05"] as const;
export type DesignId = (typeof DESIGN_IDS)[number];

export const DESIGN_META: Record<
  DesignId,
  { slug: string; title: string; previewOnly: boolean }
> = {
  d01: { slug: "bridge-console", title: "Bridge Console", previewOnly: false },
  d02: { slug: "chart-table", title: "Chart Table", previewOnly: true },
  d03: { slug: "machinery-deck", title: "Machinery Deck", previewOnly: true },
  d04: { slug: "hard-edge", title: "Hard Edge", previewOnly: true },
  d05: {
    slug: "instrument-cluster",
    title: "Instrument Cluster",
    previewOnly: true,
  },
};

export const STORAGE_THEME_KEY = "shipsense-theme";
export const STORAGE_DESIGN_KEY = "shipsense-design";

export const DEFAULT_THEME: ThemeId = "day";
export const DEFAULT_DESIGN: DesignId = "d01";

export type ThemeTokens = {
  surface0: string;
  surface1: string;
  surface2: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  borderSubtle: string;
  borderStrong: string;
  focusRing: string;
  chromeAccent: string;
  fontSans: string;
  fontMono: string;
  fontDisplay: string;
  fontDisplaySize: string;
  fontCritical: string;
  fontTitle: string;
  fontBody: string;
  fontCaption: string;
  fontMonoValue: string;
  radiusSm: string;
  radiusMd: string;
  radiusLg: string;
  borderWidth: string;
  borderWidthStrong: string;
  spaceUnit: string;
  gapGrid: string;
  panelPad: string;
  contentPadX: string;
  statusbarHeight: string;
  touchMin: string;
  alarmCriticalFg: string;
  alarmWarningFg: string;
  alarmInfoFg: string;
  qualityBadFg: string;
  qualityQuarantineFg: string;
  qualityStaleFg: string;
  qualityUncertainFg: string;
};

export const THEME_TOKEN_CSS_VARS: Record<keyof ThemeTokens, string> = {
  surface0: "--surface-0",
  surface1: "--surface-1",
  surface2: "--surface-2",
  textPrimary: "--text-primary",
  textSecondary: "--text-secondary",
  textMuted: "--text-muted",
  borderSubtle: "--border-subtle",
  borderStrong: "--border-strong",
  focusRing: "--focus-ring",
  chromeAccent: "--chrome-accent",
  fontSans: "--font-sans",
  fontMono: "--font-mono",
  fontDisplay: "--font-display",
  fontDisplaySize: "--font-display-size",
  fontCritical: "--font-critical",
  fontTitle: "--font-title",
  fontBody: "--font-body",
  fontCaption: "--font-caption",
  fontMonoValue: "--font-mono-value",
  radiusSm: "--radius-sm",
  radiusMd: "--radius-md",
  radiusLg: "--radius-lg",
  borderWidth: "--border-width",
  borderWidthStrong: "--border-width-strong",
  spaceUnit: "--space-unit",
  gapGrid: "--gap-grid",
  panelPad: "--panel-pad",
  contentPadX: "--content-pad-x",
  statusbarHeight: "--statusbar-height",
  touchMin: "--touch-min",
  alarmCriticalFg: "--alarm-critical-fg",
  alarmWarningFg: "--alarm-warning-fg",
  alarmInfoFg: "--alarm-info-fg",
  qualityBadFg: "--quality-bad-fg",
  qualityQuarantineFg: "--quality-quarantine-fg",
  qualityStaleFg: "--quality-stale-fg",
  qualityUncertainFg: "--quality-uncertain-fg",
};

export function isThemeId(value: string): value is ThemeId {
  return (THEME_IDS as readonly string[]).includes(value);
}

export function isDesignId(value: string): value is DesignId {
  return (DESIGN_IDS as readonly string[]).includes(value);
}

export function nextTheme(current: ThemeId): ThemeId {
  const i = THEME_IDS.indexOf(current);
  return THEME_IDS[(i + 1) % THEME_IDS.length];
}

export function nextDesign(current: DesignId): DesignId {
  const i = DESIGN_IDS.indexOf(current);
  return DESIGN_IDS[(i + 1) % DESIGN_IDS.length];
}
