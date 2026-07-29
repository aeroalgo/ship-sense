import type { ReactNode } from "react";

import type { LampSeverity } from "@/lib/ds/lamp-grammar-spec";

import { Lamp } from "./Lamp";

export const STATUS_BAR_TEST_ID = "status-bar";

export type StatusBarAlarm = {
  id: string;
  label: string;
  severity: LampSeverity;
  lifecycle?: "active" | "acked" | "cleared";
  quality?: "good" | "uncertain" | "bad" | "stale" | "quarantine";
};

export type StatusBarProps = {
  alarms: StatusBarAlarm[];
  onAlarmClick?: (alarm: StatusBarAlarm) => void;
  compact?: boolean;
  children?: ReactNode;
};

export function StatusBar({
  alarms,
  onAlarmClick,
  compact = false,
  children,
}: StatusBarProps) {
  return (
    <header
      data-testid={STATUS_BAR_TEST_ID}
      data-compact={compact ? "true" : "false"}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-2, 8px)",
        minHeight: compact ? 40 : 56,
        padding: "0 var(--panel-pad, 16px)",
        background: "var(--surface-0)",
        borderBottom: "var(--border-width, 1px) solid var(--border-strong)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--font-body)",
        overflowX: "auto",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-2, 8px)",
          flex: 1,
          minWidth: 0,
        }}
      >
        {alarms.length === 0 ? (
          <span style={{ color: "var(--text-muted)" }}>Нет активных тревог</span>
        ) : (
          alarms.map((alarm) => (
            <button
              key={alarm.id}
              type="button"
              data-alarm-id={alarm.id}
              onClick={() => onAlarmClick?.(alarm)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                minHeight: "var(--touch-min, 48px)",
                padding: "0 10px",
                border: "var(--border-width, 1px) solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                background: "var(--surface-1)",
                color: "var(--text-primary)",
                fontFamily: "inherit",
                fontSize: "inherit",
                cursor: onAlarmClick ? "pointer" : "default",
                whiteSpace: "nowrap",
              }}
            >
              <Lamp
                severity={alarm.severity}
                lifecycle={alarm.lifecycle ?? "active"}
                quality={alarm.quality ?? "good"}
                size={compact ? "sm" : "lg"}
              />
              {alarm.label}
            </button>
          ))
        )}
      </div>
      {children}
    </header>
  );
}
