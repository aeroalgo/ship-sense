import type { ReactNode } from "react";

export const STATE_SHELL_TEST_ID = "state-shell";

export const STATE_SHELL_VARIANTS = [
  "loading",
  "empty",
  "error",
  "partial",
  "stale",
] as const;

export type StateShellVariant = (typeof STATE_SHELL_VARIANTS)[number];

export type StateShellProps = {
  variant: StateShellVariant;
  message?: string;
  onRetry?: () => void;
  children?: ReactNode;
};

const DEFAULT_MESSAGES: Record<StateShellVariant, string> = {
  loading: "Загрузка…",
  empty: "Нет данных",
  error: "Ошибка загрузки",
  partial: "Часть данных под сверкой",
  stale: "Данные устарели",
};

export function StateShell({
  variant,
  message,
  onRetry,
  children,
}: StateShellProps) {
  const text = message ?? DEFAULT_MESSAGES[variant];

  return (
    <div
      data-testid={STATE_SHELL_TEST_ID}
      data-variant={variant}
      role="status"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-3, 12px)",
        padding: "var(--panel-pad, 16px)",
        background: "var(--surface-1)",
        color: "var(--text-primary)",
        border: "var(--border-width, 1px) solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--font-body)",
        minHeight: "var(--touch-min, 48px)",
      }}
    >
      <p style={{ margin: 0, color: "var(--text-secondary)" }}>{text}</p>
      {children}
      {variant === "error" && onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          style={{
            alignSelf: "flex-start",
            minHeight: "var(--touch-min, 48px)",
            minWidth: "var(--touch-min, 48px)",
            padding: "0 var(--panel-pad, 16px)",
            border: "var(--border-width, 1px) solid var(--border-strong)",
            borderRadius: "var(--radius-md)",
            background: "var(--surface-2)",
            color: "var(--text-primary)",
            fontFamily: "var(--font-sans)",
            fontSize: "var(--font-body)",
            cursor: "pointer",
          }}
        >
          Повторить
        </button>
      ) : null}
    </div>
  );
}
