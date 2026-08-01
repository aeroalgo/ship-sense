"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { DesignSwitcher } from "@/components/ds/DesignSwitcher";
import { LoginTile, LOGIN_TILE_TEST_ID } from "@/components/ds/LoginTile";
import { StateShell } from "@/components/ds/StateShell";
import { ThemeSwitcher } from "@/components/ds/ThemeSwitcher";
import { useDesign } from "@/hooks/useDesign";
import { useTheme } from "@/hooks/useTheme";
import { ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/query-keys";
import { fetchRoster } from "@/lib/api/session";

import { useSession } from "./useSession";

export const LOGIN_PAGE_TEST_ID = "login-page";

export function LoginPage() {
  const router = useRouter();
  const { person, login } = useSession();
  const { theme, setTheme } = useTheme();
  const { design, setDesign } = useDesign();
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const roster = useQuery({
    queryKey: queryKeys.roster,
    queryFn: async ({ signal }) => {
      const result = await fetchRoster(signal);
      return result.data;
    },
    retry: false,
  });

  const tiles = useMemo(() => {
    const items = roster.data?.items ?? [];
    return items
      .filter((item) => item.active)
      .sort((a, b) => a.tile_order - b.tile_order);
  }, [roster.data]);

  async function onSelect(personId: string) {
    if (pendingId) return;
    setSubmitError(null);
    setPendingId(personId);
    try {
      const path = await login(personId);
      router.push(path);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Не удалось создать сессию";
      setSubmitError(message);
    } finally {
      setPendingId(null);
    }
  }

  if (roster.isLoading) {
    return <StateShell variant="loading" message="Загрузка списка вахты…" />;
  }

  if (roster.isError) {
    return (
      <StateShell
        variant="error"
        message="Не удалось загрузить список вахты"
        onRetry={() => void roster.refetch()}
      />
    );
  }

  if (tiles.length === 0) {
    return <StateShell variant="empty" message="Нет доступных плиток входа" />;
  }

  return (
    <div
      data-testid={LOGIN_PAGE_TEST_ID}
      style={{
        minHeight: "100dvh",
        padding: "var(--panel-pad, 16px)",
        background: "var(--surface-0)",
        color: "var(--text-primary)",
        fontFamily: "var(--font-sans)",
      }}
    >
      <header style={{ marginBottom: 24 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            flexWrap: "wrap",
            marginBottom: 16,
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: "var(--font-caption, 14px)",
              letterSpacing: "var(--tracking-label, 0.04em)",
              textTransform: "uppercase",
              color: "var(--chrome-accent, var(--text-secondary))",
              fontWeight: 600,
            }}
          >
            ShipSense
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <ThemeSwitcher theme={theme} onChange={setTheme} />
            <DesignSwitcher design={design} onChange={setDesign} />
          </div>
        </div>
        <h1
          style={{
            margin: 0,
            fontSize: "var(--font-title, 1.5rem)",
            fontWeight: 600,
          }}
        >
          Вход на вахту
        </h1>
        <p
          style={{
            margin: "8px 0 0",
            color: "var(--text-secondary)",
            fontSize: "var(--font-body)",
          }}
        >
          Выберите плитку. Сессия откроется сразу.
        </p>
      </header>

      {submitError ? (
        <p
          role="alert"
          style={{
            marginBottom: 16,
            color: "var(--status-bad, #c62828)",
            fontSize: "var(--font-body)",
          }}
        >
          {submitError}
        </p>
      ) : null}

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        {tiles.map((tile) => (
          <LoginTile
            key={tile.person_id}
            person={tile.name}
            personId={tile.person_id}
            rank={tile.rank}
            active={
              pendingId === tile.person_id ||
              person?.person_id === tile.person_id
            }
            onSelect={onSelect}
          />
        ))}
      </div>

      <span data-testid={`${LOGIN_TILE_TEST_ID}-count`} hidden>
        {tiles.length}
      </span>
    </div>
  );
}
