"use client";

import { THEME_SWITCHER_TEST_ID } from "@/lib/theme/switcher-spec";
import { nextTheme, type ThemeId } from "@/lib/theme/types";

export type ThemeSwitcherProps = {
  theme: ThemeId;
  onChange: (theme: ThemeId) => void;
};

export function ThemeSwitcher({ theme, onChange }: ThemeSwitcherProps) {
  return (
    <button
      type="button"
      data-testid={THEME_SWITCHER_TEST_ID}
      aria-label="Тема освещения"
      onClick={() => onChange(nextTheme(theme))}
      style={{
        minWidth: "var(--touch-min, 48px)",
        minHeight: "var(--touch-min, 48px)",
        padding: "0 var(--panel-pad, 16px)",
        border: "var(--border-width, 1px) solid var(--border-strong)",
        borderRadius: "var(--radius-md)",
        background: "var(--surface-1)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--font-body)",
        cursor: "pointer",
      }}
    >
      {theme}
    </button>
  );
}
