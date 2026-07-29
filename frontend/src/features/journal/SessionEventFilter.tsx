"use client";

import type { CSSProperties } from "react";

export const SESSION_EVENT_FILTER_TEST_ID = "session-event-filter";

export type SessionEventFilterProps = {
  active: boolean;
  onToggle: () => void;
};

export function SessionEventFilter({
  active,
  onToggle,
}: SessionEventFilterProps) {
  const style: CSSProperties = {
    minHeight: "var(--touch-min, 48px)",
    minWidth: "var(--touch-min, 48px)",
    padding: "0 14px",
    border: "var(--border-width, 1px) solid var(--border-subtle)",
    borderRadius: "var(--radius-sm)",
    background: active ? "var(--surface-2)" : "var(--surface-1)",
    color: "var(--text-primary)",
    fontFamily: "var(--font-sans)",
    fontSize: "var(--font-body)",
    fontWeight: active ? 600 : 400,
    cursor: "pointer",
    borderLeft: active
      ? "4px solid var(--text-secondary)"
      : "4px solid transparent",
  };

  return (
    <button
      type="button"
      data-testid={SESSION_EVENT_FILTER_TEST_ID}
      aria-pressed={active}
      onClick={onToggle}
      style={style}
    >
      Смены
    </button>
  );
}
