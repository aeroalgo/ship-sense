"use client";

import { useState, type ReactNode } from "react";

export const WATCH_SECTION_TEST_ID = "watch-section";

export type WatchSectionItem = {
  id: string;
  label: string;
  detail?: string;
};

export type WatchSectionProps = {
  title: string;
  items: WatchSectionItem[];
  collapsible?: boolean;
  defaultOpen?: boolean;
  children?: ReactNode;
};

export function WatchSection({
  title,
  items,
  collapsible = false,
  defaultOpen = true,
  children,
}: WatchSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section
      data-testid={WATCH_SECTION_TEST_ID}
      data-open={open ? "true" : "false"}
      style={{
        background: "var(--surface-1)",
        border: "var(--border-width, 1px) solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-sans)",
      }}
    >
      {collapsible ? (
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            minHeight: "var(--touch-min, 48px)",
            padding: "0 var(--panel-pad, 16px)",
            background: "transparent",
            border: "none",
            color: "inherit",
            fontFamily: "inherit",
            fontSize: "var(--font-body)",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          <span>{title}</span>
          <span aria-hidden="true">{open ? "▾" : "▸"}</span>
        </button>
      ) : (
        <h3
          style={{
            margin: 0,
            padding: "12px var(--panel-pad, 16px)",
            fontSize: "var(--font-body)",
            fontWeight: 600,
          }}
        >
          {title}
        </h3>
      )}
      {open ? (
        <ul
          style={{
            listStyle: "none",
            margin: 0,
            padding: "0 var(--panel-pad, 16px) 12px",
          }}
        >
          {items.map((item) => (
            <li
              key={item.id}
              style={{
                minHeight: 40,
                display: "flex",
                justifyContent: "space-between",
                gap: 8,
                padding: "6px 0",
                borderTop: "var(--border-width, 1px) solid var(--border-subtle)",
              }}
            >
              <span>{item.label}</span>
              {item.detail ? (
                <span style={{ color: "var(--text-secondary)" }}>
                  {item.detail}
                </span>
              ) : null}
            </li>
          ))}
          {children}
        </ul>
      ) : null}
    </section>
  );
}
