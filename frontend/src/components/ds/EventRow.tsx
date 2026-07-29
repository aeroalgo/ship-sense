import type { EventItem } from "@/lib/api/types";
import type { LampSeverity } from "@/lib/ds/lamp-grammar-spec";

import { Lamp } from "./Lamp";

export const EVENT_ROW_TEST_ID = "event-row";

function mapEventSeverity(
  severity: EventItem["severity"],
): LampSeverity {
  if (severity === "alarm") return "alarm";
  if (severity === "warning") return "warning-drift";
  if (severity === "info") return "info";
  return "no-data";
}

export type EventRowProps = {
  event: EventItem;
  onTrendClick?: (event: EventItem) => void;
};

export function EventRow({ event, onTrendClick }: EventRowProps) {
  const quality = event.quality ?? "good";

  return (
    <div
      data-testid={EVENT_ROW_TEST_ID}
      data-event-id={event.id}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-2, 8px)",
        minHeight: "var(--touch-min, 48px)",
        padding: "8px var(--panel-pad, 16px)",
        borderBottom: "var(--border-width, 1px) solid var(--border-subtle)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-mono, var(--font-sans))",
        fontSize: "var(--font-body)",
        background: "var(--surface-0)",
      }}
    >
      <Lamp
        severity={mapEventSeverity(event.severity)}
        lifecycle="active"
        quality={quality}
        size="sm"
      />
      <time dateTime={event.ts} style={{ color: "var(--text-secondary)" }}>
        {event.ts}
      </time>
      <span style={{ flex: 1 }}>{event.event_name}</span>
      <span style={{ color: "var(--text-muted)" }}>{event.source}</span>
      {onTrendClick ? (
        <button
          type="button"
          onClick={() => onTrendClick(event)}
          style={{
            minHeight: "var(--touch-min, 48px)",
            minWidth: "var(--touch-min, 48px)",
            border: "var(--border-width, 1px) solid var(--border-subtle)",
            borderRadius: "var(--radius-sm)",
            background: "var(--surface-1)",
            color: "var(--text-primary)",
            cursor: "pointer",
            fontFamily: "var(--font-sans)",
          }}
        >
          Тренд
        </button>
      ) : null}
    </div>
  );
}
