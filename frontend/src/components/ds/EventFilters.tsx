import type { CSSProperties } from "react";

export const JOURNAL_FILTERS_TEST_ID = "journal-filters";

export type EventFiltersValue = {
  eventName?: string;
  severity?: "info" | "warning" | "alarm" | "";
  assetId?: string;
  source?: string;
  from?: string;
  to?: string;
};

export type EventFiltersProps = {
  filters: EventFiltersValue;
  onChange: (next: EventFiltersValue) => void;
  onPrint?: () => void;
};

export function EventFilters({
  filters,
  onChange,
  onPrint,
}: EventFiltersProps) {
  const fieldStyle: CSSProperties = {
    minHeight: "var(--touch-min, 48px)",
    padding: "0 10px",
    border: "var(--border-width, 1px) solid var(--border-subtle)",
    borderRadius: "var(--radius-sm)",
    background: "var(--surface-1)",
    color: "var(--text-primary)",
    fontFamily: "var(--font-sans)",
    fontSize: "var(--font-body)",
  };

  return (
    <form
      data-testid={JOURNAL_FILTERS_TEST_ID}
      onSubmit={(e) => e.preventDefault()}
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "var(--space-2, 8px)",
        alignItems: "center",
        padding: "var(--panel-pad, 16px)",
        background: "var(--surface-0)",
        borderBottom: "var(--border-width, 1px) solid var(--border-subtle)",
      }}
    >
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ color: "var(--text-secondary)", fontSize: "var(--font-caption, 0.875rem)" }}>
          Тип
        </span>
        <input
          value={filters.eventName ?? ""}
          onChange={(e) =>
            onChange({ ...filters, eventName: e.target.value })
          }
          style={fieldStyle}
        />
      </label>
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ color: "var(--text-secondary)", fontSize: "var(--font-caption, 0.875rem)" }}>
          Severity
        </span>
        <select
          value={filters.severity ?? ""}
          onChange={(e) =>
            onChange({
              ...filters,
              severity: e.target.value as EventFiltersValue["severity"],
            })
          }
          style={fieldStyle}
        >
          <option value="">Все</option>
          <option value="info">info</option>
          <option value="warning">warning</option>
          <option value="alarm">alarm</option>
        </select>
      </label>
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ color: "var(--text-secondary)", fontSize: "var(--font-caption, 0.875rem)" }}>
          Система
        </span>
        <input
          value={filters.assetId ?? ""}
          onChange={(e) => onChange({ ...filters, assetId: e.target.value })}
          style={fieldStyle}
        />
      </label>
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ color: "var(--text-secondary)", fontSize: "var(--font-caption, 0.875rem)" }}>
          С
        </span>
        <input
          type="datetime-local"
          value={filters.from ?? ""}
          onChange={(e) => onChange({ ...filters, from: e.target.value })}
          style={fieldStyle}
        />
      </label>
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ color: "var(--text-secondary)", fontSize: "var(--font-caption, 0.875rem)" }}>
          По
        </span>
        <input
          type="datetime-local"
          value={filters.to ?? ""}
          onChange={(e) => onChange({ ...filters, to: e.target.value })}
          style={fieldStyle}
        />
      </label>
      {onPrint ? (
        <button
          type="button"
          data-testid="print-button"
          onClick={onPrint}
          style={{
            ...fieldStyle,
            marginTop: 18,
            cursor: "pointer",
          }}
        >
          Печать
        </button>
      ) : null}
    </form>
  );
}
