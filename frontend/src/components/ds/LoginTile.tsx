export const LOGIN_TILE_TEST_ID = "login-tile";

export type LoginTileProps = {
  person: string;
  personId: string;
  rank: string;
  active?: boolean;
  onSelect?: (personId: string) => void;
};

export function LoginTile({
  person,
  personId,
  rank,
  active = false,
  onSelect,
}: LoginTileProps) {
  return (
    <button
      type="button"
      data-testid={LOGIN_TILE_TEST_ID}
      data-person-id={personId}
      data-active={active ? "true" : "false"}
      onClick={() => onSelect?.(personId)}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        gap: 4,
        minWidth: 160,
        minHeight: 96,
        padding: "var(--panel-pad, 16px)",
        background: active ? "var(--surface-2)" : "var(--surface-1)",
        color: "var(--text-primary)",
        border: `var(--border-width, 1px) solid ${
          active ? "var(--border-strong)" : "var(--border-subtle)"
        }`,
        borderRadius: "var(--radius-md)",
        fontFamily: "var(--font-sans)",
        textAlign: "left",
        cursor: "pointer",
      }}
    >
      <span style={{ fontSize: "var(--font-title, 1.25rem)", fontWeight: 600 }}>
        {person}
      </span>
      <span style={{ color: "var(--text-secondary)", fontSize: "var(--font-body)" }}>
        {rank}
      </span>
    </button>
  );
}
