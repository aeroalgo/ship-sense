import type { DesignId, ThemeId } from "./types";

export type ThemeSwitcherProps = {
  theme: ThemeId;
  onChange: (theme: ThemeId) => void;
};

export type DesignSwitcherProps = {
  design: DesignId;
  onChange: (design: DesignId) => void;
  enabled?: boolean;
};

export const THEME_SWITCHER_TEST_ID = "theme-switcher";
export const DESIGN_SWITCHER_TEST_ID = "design-switcher";

export const DESIGN_PREVIEW_ENV = "NEXT_PUBLIC_DESIGN_PREVIEW";

export function isDesignPreviewEnabled(
  env?: Record<string, string | undefined>,
): boolean {
  const previewFlag =
    env?.[DESIGN_PREVIEW_ENV] ?? process.env.NEXT_PUBLIC_DESIGN_PREVIEW;
  if (previewFlag === "1") return true;

  const nodeEnv = env?.NODE_ENV ?? process.env.NODE_ENV;
  if (nodeEnv === "development") return true;

  return false;
}
