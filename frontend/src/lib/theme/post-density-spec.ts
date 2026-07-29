export const WORST_VIEW_DISTANCE_M = 2.5;
export const VISUAL_RATIO_DENOM = 200;
export const CSS_DPI = 96;
export const MM_PER_INCH = 25.4;
export const TOUCH_MIN_MM = 15;

export const FONT_DISPLAY_FLOOR_PX = 56;
export const FONT_CRITICAL_FLOOR_PX = 48;
export const FONT_TITLE_FLOOR_PX = 28;
export const FONT_BODY_FLOOR_PX = 18;
export const FONT_CAPTION_FLOOR_PX = 14;
export const FONT_MONO_VALUE_FLOOR_PX = 20;

export const TOUCH_MIN_FLOOR_PX = 57;
export const OVERVIEW_GROUP_MIN_W_PX = 176;
export const OVERVIEW_GROUP_MIN_H_PX = 128;

export const POST_DENSITY_WAIVER = {
  reason: "Q9 field measurements not collected",
  assumedPosts: 6,
  diagonalIn: 24,
  resolution: "1920x1080",
  distanceM: WORST_VIEW_DISTANCE_M,
  input: "touch",
  seaState: "medium",
} as const;

export function mmToCssPx(mm: number, dpi: number = CSS_DPI): number {
  return Math.ceil((mm * dpi) / MM_PER_INCH);
}

export function criticalHeightMm(
  distanceM: number = WORST_VIEW_DISTANCE_M,
  ratioDenom: number = VISUAL_RATIO_DENOM,
): number {
  return (distanceM * 1000) / ratioDenom;
}

export function criticalFontPx(
  distanceM: number = WORST_VIEW_DISTANCE_M,
): number {
  return mmToCssPx(criticalHeightMm(distanceM));
}

export function touchMinPx(minMm: number = TOUCH_MIN_MM): number {
  return mmToCssPx(minMm);
}

export type TypeScalePx = {
  display: number;
  critical: number;
  title: number;
  body: number;
  caption: number;
  monoValue: number;
};

export const CANONICAL_TYPE_SCALE_PX: TypeScalePx = {
  display: FONT_DISPLAY_FLOOR_PX,
  critical: FONT_CRITICAL_FLOOR_PX,
  title: 32,
  body: FONT_BODY_FLOOR_PX,
  caption: FONT_CAPTION_FLOOR_PX,
  monoValue: 22,
};

export function assertMeetsDensityFloor(scale: TypeScalePx): void {
  if (scale.critical < FONT_CRITICAL_FLOOR_PX) {
    throw new Error(
      `font-critical ${scale.critical}px < floor ${FONT_CRITICAL_FLOOR_PX}px (G-DS0-2-02)`,
    );
  }
  if (scale.display < FONT_DISPLAY_FLOOR_PX) {
    throw new Error(
      `font-display ${scale.display}px < floor ${FONT_DISPLAY_FLOOR_PX}px`,
    );
  }
  if (scale.title < FONT_TITLE_FLOOR_PX) {
    throw new Error(
      `font-title ${scale.title}px < floor ${FONT_TITLE_FLOOR_PX}px`,
    );
  }
  if (scale.body < FONT_BODY_FLOOR_PX) {
    throw new Error(
      `font-body ${scale.body}px < floor ${FONT_BODY_FLOOR_PX}px`,
    );
  }
  if (scale.caption < FONT_CAPTION_FLOOR_PX) {
    throw new Error(
      `font-caption ${scale.caption}px < floor ${FONT_CAPTION_FLOOR_PX}px`,
    );
  }
  if (scale.monoValue < FONT_MONO_VALUE_FLOOR_PX) {
    throw new Error(
      `font-mono-value ${scale.monoValue}px < floor ${FONT_MONO_VALUE_FLOOR_PX}px`,
    );
  }
}

export function assertComputedFloorsMatchCanon(): void {
  const critical = criticalFontPx();
  const touch = touchMinPx();
  if (critical !== FONT_CRITICAL_FLOOR_PX) {
    throw new Error(
      `computed critical ${critical}px !== canon floor ${FONT_CRITICAL_FLOOR_PX}px`,
    );
  }
  if (touch !== TOUCH_MIN_FLOOR_PX) {
    throw new Error(
      `computed touch ${touch}px !== canon floor ${TOUCH_MIN_FLOOR_PX}px`,
    );
  }
  assertMeetsDensityFloor(CANONICAL_TYPE_SCALE_PX);
}
