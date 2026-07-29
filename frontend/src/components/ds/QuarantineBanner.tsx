export const QUARANTINE_BANNER_TEST_ID = "quarantine-banner";

export type QuarantineBannerProps = {
  tags: string[];
  scope?: string;
};

export function QuarantineBanner({
  tags,
  scope = "экран",
}: QuarantineBannerProps) {
  if (tags.length === 0) return null;

  return (
    <div
      data-testid={QUARANTINE_BANNER_TEST_ID}
      data-count={tags.length}
      role="status"
      style={{
        padding: "10px var(--panel-pad, 16px)",
        background: "var(--quality-quarantine-bg, var(--surface-2))",
        color: "var(--quality-quarantine-fg, var(--text-primary))",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--font-body)",
        borderBottom: "var(--border-width, 1px) solid var(--border-subtle)",
      }}
    >
      {tags.length} тегов под сверкой ({scope}): группы помечены
    </div>
  );
}
