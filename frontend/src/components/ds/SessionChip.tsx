export const SESSION_CHIP_TEST_ID = "session-chip";

export type SessionChipProps = {
  name: string;
  rank: string;
  onLogout?: () => void;
};

export function SessionChip({ name, rank, onLogout }: SessionChipProps) {
  return (
    <div
      data-testid={SESSION_CHIP_TEST_ID}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        minHeight: "var(--touch-min, 48px)",
        padding: "0 12px",
        background: "var(--surface-1)",
        color: "var(--text-primary)",
        border: "var(--border-width, 1px) solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--font-body)",
      }}
    >
      <span>
        {name}
        <span style={{ color: "var(--text-secondary)" }}> · {rank}</span>
      </span>
      {onLogout ? (
        <button
          type="button"
          onClick={onLogout}
          aria-label="Выйти"
          style={{
            minHeight: "var(--touch-min, 48px)",
            minWidth: "var(--touch-min, 48px)",
            border: "none",
            background: "transparent",
            color: "var(--text-secondary)",
            cursor: "pointer",
            fontFamily: "inherit",
          }}
        >
          Выйти
        </button>
      ) : null}
    </div>
  );
}
