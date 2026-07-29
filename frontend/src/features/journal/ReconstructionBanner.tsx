export const RECONSTRUCTION_BANNER_TEST_ID = "reconstruction-banner";

export const RECONSTRUCTION_BANNER_COPY =
  "Журнал: реконструкция по состояниям";

export type ReconstructionBannerProps = {
  mode?: string | null;
};

export function ReconstructionBanner({
  mode = "edge_only",
}: ReconstructionBannerProps) {
  if (!mode) return null;

  return (
    <div
      data-testid={RECONSTRUCTION_BANNER_TEST_ID}
      data-mode={mode}
      role="status"
      style={{
        padding: "12px var(--panel-pad, 16px)",
        borderBottom: "var(--border-width, 1px) solid var(--border-subtle)",
        background: "var(--surface-2)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--font-body)",
      }}
    >
      {RECONSTRUCTION_BANNER_COPY}
    </div>
  );
}
