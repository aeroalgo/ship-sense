"use client";

import { DESIGN_SWITCHER_TEST_ID } from "@/lib/theme/switcher-spec";
import {
  DESIGN_META,
  nextDesign,
  type DesignId,
} from "@/lib/theme/types";

export type DesignSwitcherProps = {
  design: DesignId;
  onChange: (design: DesignId) => void;
  enabled?: boolean;
};

export function DesignSwitcher({
  design,
  onChange,
  enabled = true,
}: DesignSwitcherProps) {
  if (!enabled) return null;

  return (
    <button
      type="button"
      data-testid={DESIGN_SWITCHER_TEST_ID}
      aria-label="Дизайн-скин"
      onClick={() => onChange(nextDesign(design))}
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
      {DESIGN_META[design].title}
    </button>
  );
}
