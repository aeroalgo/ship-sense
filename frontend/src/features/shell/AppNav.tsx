"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export const APP_NAV_TEST_ID = "app-nav";

export const NAV_ITEMS = [
  { href: "/overview", label: "Обзор", testId: "nav-overview" },
  { href: "/journal", label: "Журнал", testId: "nav-journal" },
  { href: "/trends", label: "Тренды", testId: "nav-trends" },
  { href: "/watch", label: "Вахтенный", testId: "nav-watch" },
] as const;

export type NavItem = (typeof NAV_ITEMS)[number];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav
      data-testid={APP_NAV_TEST_ID}
      aria-label="Основная навигация"
      style={{
        display: "flex",
        alignItems: "stretch",
        gap: "var(--space-1, 4px)",
        padding: "0 var(--panel-pad, 16px)",
        background: "var(--surface-0)",
        borderBottom: "var(--border-width, 1px) solid var(--border-strong)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--font-body)",
      }}
    >
      {NAV_ITEMS.map((item) => {
        const active =
          pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            data-testid={item.testId}
            data-active={active ? "true" : "false"}
            className={active ? "app-nav__link--active" : undefined}
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              minHeight: "var(--touch-min, 48px)",
              minWidth: "var(--touch-min, 48px)",
              padding: "0 16px",
              color: active ? "var(--text-primary)" : "var(--text-secondary)",
              textDecoration: "none",
              borderBottom: active
                ? "2px solid var(--accent, var(--border-strong))"
                : "2px solid transparent",
              fontWeight: active ? 600 : 400,
            }}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
