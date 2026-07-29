import {
  resolveGroupLamp,
  type LampQuality,
  type LampSeverity,
} from "@/lib/ds/lamp-grammar-spec";
import type { AggregateStatus } from "@/lib/quality/types";

import { Lamp } from "./Lamp";

export const SHIP_STATUS_TEST_ID = "ship-status";

export type AggregateShipStatusProps = {
  status: AggregateStatus;
  label: string;
  worstSeverity?: LampSeverity | null;
};

export function AggregateShipStatus({
  status,
  label,
  worstSeverity = null,
}: AggregateShipStatusProps) {
  const lamp = resolveGroupLamp({
    aggregateQuality: status as LampQuality | "unknown",
    worstSeverity,
  });

  return (
    <div
      data-testid={SHIP_STATUS_TEST_ID}
      data-status={status}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-3, 12px)",
        padding: "var(--panel-pad, 16px)",
        background: "var(--surface-1)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--font-title, 1.25rem)",
        borderRadius: "var(--radius-md)",
      }}
    >
      <Lamp
        severity={lamp.severity}
        lifecycle={lamp.lifecycle}
        quality={lamp.quality}
        size="xl"
      />
      <span>{label}</span>
    </div>
  );
}
