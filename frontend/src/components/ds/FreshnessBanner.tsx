export const FRESHNESS_BANNER_TEST_ID = "freshness-banner";

export type FreshnessBannerProps = {
  lastTs: string | null;
  stale: boolean;
  message?: string;
};

export function FreshnessBanner({
  lastTs,
  stale,
  message,
}: FreshnessBannerProps) {
  if (!stale && !message) return null;

  const text =
    message ??
    (stale
      ? `Связь устарела${lastTs ? ` (последнее: ${lastTs})` : ""}`
      : `Актуально: ${lastTs ?? "-"}`);

  return (
    <div
      data-testid={FRESHNESS_BANNER_TEST_ID}
      data-stale={stale ? "true" : "false"}
      role="status"
      style={{
        padding: "10px var(--panel-pad, 16px)",
        background: stale
          ? "var(--quality-stale-bg, var(--surface-2))"
          : "var(--surface-1)",
        color: stale
          ? "var(--quality-stale-fg, var(--text-primary))"
          : "var(--text-secondary)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--font-body)",
        borderBottom: "var(--border-width, 1px) solid var(--border-subtle)",
      }}
    >
      {text}
    </div>
  );
}
