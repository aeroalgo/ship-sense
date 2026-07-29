import {
  DATA_QUALITY_PANEL_TEST_ID,
} from "./debounce";

export type DataQualityPanelProps = {
  quarantine_tags: string[];
  stale_intervals: Array<{ from: string; to: string }>;
  banner: string;
};

export function DataQualityPanel({
  quarantine_tags,
  stale_intervals,
  banner,
}: DataQualityPanelProps) {
  return (
    <section
      data-testid={DATA_QUALITY_PANEL_TEST_ID}
      style={{
        background: "var(--surface-1)",
        border: "var(--border-width, 1px) solid var(--border-subtle)",
        borderLeft: "4px solid var(--alarm-warning-fg)",
        borderRadius: "var(--radius-md)",
        padding: "var(--panel-pad, 16px)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-sans)",
      }}
    >
      <h3
        style={{
          margin: "0 0 8px",
          fontSize: "var(--font-body)",
          fontWeight: 600,
        }}
      >
        Качество данных
      </h3>
      {banner ? (
        <p
          style={{
            margin: "0 0 12px",
            color: "var(--alarm-warning-fg)",
            fontSize: "var(--font-body)",
          }}
        >
          {banner}
        </p>
      ) : null}
      <dl
        style={{
          margin: 0,
          display: "grid",
          gap: 8,
          fontSize: "var(--font-caption, 0.875rem)",
          color: "var(--text-secondary)",
        }}
      >
        <div>
          <dt style={{ fontWeight: 600, color: "var(--text-primary)" }}>
            quarantine_tags
          </dt>
          <dd style={{ margin: "2px 0 0" }}>
            {quarantine_tags.length > 0
              ? quarantine_tags.join(", ")
              : "-"}
          </dd>
        </div>
        <div>
          <dt style={{ fontWeight: 600, color: "var(--text-primary)" }}>
            stale_intervals
          </dt>
          <dd style={{ margin: "2px 0 0" }}>
            {stale_intervals.length > 0
              ? stale_intervals
                  .map((iv) => `${iv.from} → ${iv.to}`)
                  .join("; ")
              : "-"}
          </dd>
        </div>
      </dl>
    </section>
  );
}
