"use client";

import type { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { DesignSwitcher } from "@/components/ds/DesignSwitcher";
import { SessionChip } from "@/components/ds/SessionChip";
import { StatusBar } from "@/components/ds/StatusBar";
import { ThemeSwitcher } from "@/components/ds/ThemeSwitcher";
import { useSession } from "@/features/session/useSession";
import { useDesign } from "@/hooks/useDesign";
import { useTheme } from "@/hooks/useTheme";

import { AppNav } from "./AppNav";
import { APP_ROOT_ID } from "./FreshnessController";
import { useStatusBarAlarms } from "./useStatusBarAlarms";
import type { StatusBarAlarmItem } from "./useStatusBarAlarms";

export const WS_STATUS_TEST_ID = "ws-status";
export const APP_SHELL_TEST_ID = "app-shell";

function journalHrefFromAlarm(alarm: StatusBarAlarmItem): string {
  const params = new URLSearchParams();
  if (alarm.assetId) params.set("asset_id", alarm.assetId);
  if (alarm.from) params.set("from", alarm.from);
  const qs = params.toString();
  return qs ? `/journal?${qs}` : "/journal";
}

export type AppShellProps = {
  children: ReactNode;
  freshnessSlot?: ReactNode;
};

export function AppShell({ children, freshnessSlot }: AppShellProps) {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const { design, setDesign } = useDesign();
  const { person, isReady, logout } = useSession();
  const { alarms, wsStatus } = useStatusBarAlarms();

  useEffect(() => {
    if (isReady && !person) router.replace("/login");
  }, [isReady, person, router]);

  if (!isReady || !person) return null;

  return (
    <div
      data-testid={APP_SHELL_TEST_ID}
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100dvh",
        background: "var(--surface-0)",
        color: "var(--text-primary)",
      }}
    >
      <div
        style={{
          position: "sticky",
          top: 0,
          zIndex: 20,
          background: "var(--surface-0)",
        }}
      >
        <StatusBar
          alarms={alarms}
          onAlarmClick={(alarm) => {
            const item = alarms.find((a) => a.id === alarm.id);
            if (!item) return;
            router.push(journalHrefFromAlarm(item));
          }}
        >
          <span
            data-testid={WS_STATUS_TEST_ID}
            data-status={wsStatus}
            style={{
              color: "var(--text-muted)",
              fontSize: "var(--font-caption, 12px)",
              whiteSpace: "nowrap",
              padding: "0 8px",
            }}
          >
            {wsStatus}
          </span>
          {person ? (
            <SessionChip
              name={person.name}
              rank={person.rank}
              onLogout={() => {
                void logout().then(() => {
                  router.push("/login");
                });
              }}
            />
          ) : null}
          <ThemeSwitcher theme={theme} onChange={setTheme} />
          <DesignSwitcher design={design} onChange={setDesign} />
        </StatusBar>
        <AppNav />
        {freshnessSlot}
      </div>
      <div
        id={APP_ROOT_ID}
        style={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <main style={{ flex: 1, minHeight: 0 }}>{children}</main>
      </div>
    </div>
  );
}
