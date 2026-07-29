import {
  resolveGroupLamp,
  type LampQuality,
  type LampSeverity,
} from "@/lib/ds/lamp-grammar-spec";
import type { AggregateStatus } from "@/lib/quality/types";

import { Lamp } from "./Lamp";

export const OVERVIEW_GROUP_TEST_ID = "overview-group";

export type OverviewGroupCardProps = {
  name: string;
  status: AggregateStatus;
  alarmCount?: number;
  worstSeverity?: LampSeverity | null;
  onClick?: () => void;
};

export function OverviewGroupCard({
  name,
  status,
  alarmCount = 0,
  worstSeverity = null,
  onClick,
}: OverviewGroupCardProps) {
  const lamp = resolveGroupLamp({
    aggregateQuality: status as LampQuality | "unknown",
    worstSeverity,
  });

  return (
    <button
      type="button"
      data-testid={OVERVIEW_GROUP_TEST_ID}
      data-status={status}
      onClick={onClick}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        gap: "var(--space-2, 8px)",
        minHeight: "var(--overview-group-min-h, 128px)",
        minWidth: "var(--overview-group-min-w, 176px)",
        padding: "var(--panel-pad, 16px)",
        background: "var(--surface-1)",
        color: "var(--text-primary)",
        border: "var(--border-width, 1px) solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--font-body)",
        textAlign: "left",
        cursor: onClick ? "pointer" : "default",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Lamp
          severity={lamp.severity}
          lifecycle={lamp.lifecycle}
          quality={lamp.quality}
          size="md"
        />
        <span>{name}</span>
      </div>
      {alarmCount > 0 ? (
        <span
          data-alarm-count={alarmCount}
          style={{
            color: "var(--alarm-critical-fg)",
            fontSize: "var(--font-caption, 0.875rem)",
          }}
        >
          {alarmCount}
        </span>
      ) : null}
    </button>
  );
}
