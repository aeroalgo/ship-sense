export const WATCH_VERDICT_TEST_ID = "watch-verdict";

export type WatchVerdictTone = "ok" | "attention" | "critical";

export type WatchVerdictProps = {
  text: string;
  tone?: WatchVerdictTone;
};

const TONE_COLOR: Record<WatchVerdictTone, string> = {
  ok: "var(--text-secondary)",
  attention: "var(--alarm-warning-fg)",
  critical: "var(--alarm-critical-fg)",
};

export function WatchVerdict({ text, tone = "ok" }: WatchVerdictProps) {
  return (
    <p
      data-testid={WATCH_VERDICT_TEST_ID}
      data-tone={tone}
      style={{
        margin: 0,
        padding: "var(--panel-pad, 16px)",
        color: TONE_COLOR[tone],
        fontFamily: "var(--font-sans)",
        fontSize: "var(--font-title, 1.25rem)",
        fontWeight: 600,
        background: "var(--surface-1)",
        borderLeft: `4px solid ${TONE_COLOR[tone]}`,
      }}
    >
      {text}
    </p>
  );
}
