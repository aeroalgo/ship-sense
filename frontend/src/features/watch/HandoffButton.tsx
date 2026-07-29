"use client";

import Link from "next/link";
import type { CSSProperties } from "react";

import {
  HANDOFF_ACTIVE_ALARMS,
  HANDOFF_ACTIVE_NOW,
} from "@/lib/routing/handoff";

export const HANDOFF_BUTTON_TEST_ID = "handoff-button";

const linkBase: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minHeight: "var(--touch-min, 48px)",
  minWidth: "var(--touch-min, 48px)",
  padding: "0 16px",
  border: "var(--border-width, 1px) solid var(--border-subtle)",
  textDecoration: "none",
  fontFamily: "var(--font-sans)",
  fontSize: "var(--font-body)",
  cursor: "pointer",
};

export function HandoffButton() {
  return (
    <nav
      data-testid={HANDOFF_BUTTON_TEST_ID}
      aria-label="Пересменочный переход"
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: 12,
        alignItems: "center",
      }}
    >
      <Link
        href={HANDOFF_ACTIVE_ALARMS.href}
        data-testid={HANDOFF_ACTIVE_ALARMS.testId}
        style={{
          ...linkBase,
          background: "var(--surface-1)",
          color: "var(--text-primary)",
          borderLeft: "4px solid var(--alarm-alarm-fg, var(--text-primary))",
          fontWeight: 600,
        }}
      >
        {HANDOFF_ACTIVE_ALARMS.label}
      </Link>
      <Link
        href={HANDOFF_ACTIVE_NOW.href}
        data-testid={HANDOFF_ACTIVE_NOW.testId}
        style={{
          ...linkBase,
          background: "var(--surface-0)",
          color: "var(--text-secondary)",
        }}
      >
        {HANDOFF_ACTIVE_NOW.label}
      </Link>
    </nav>
  );
}
