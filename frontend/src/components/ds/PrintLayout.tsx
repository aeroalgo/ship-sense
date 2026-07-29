import type { ReactNode } from "react";

export const PRINT_LAYOUT_TEST_ID = "print-layout";

export type PrintLayoutProps = {
  children: ReactNode;
  provenance?: string;
  title?: string;
};

export function PrintLayout({
  children,
  provenance,
  title,
}: PrintLayoutProps) {
  return (
    <div
      data-testid={PRINT_LAYOUT_TEST_ID}
      style={{
        color: "var(--text-primary)",
        background: "var(--surface-0)",
        fontFamily: "var(--font-sans)",
        padding: "var(--panel-pad, 16px)",
      }}
    >
      {title ? (
        <h1 style={{ margin: "0 0 12px", fontSize: "var(--font-title, 1.25rem)" }}>
          {title}
        </h1>
      ) : null}
      {provenance ? (
        <p
          data-provenance="true"
          style={{
            margin: "0 0 16px",
            color: "var(--text-secondary)",
            fontSize: "var(--font-caption, 0.875rem)",
          }}
        >
          {provenance}
        </p>
      ) : null}
      {children}
    </div>
  );
}
